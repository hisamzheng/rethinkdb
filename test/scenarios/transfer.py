#!/usr/bin/python
import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'common')))
import http_admin, driver, workload_runner, scenario_common
from vcoptparse import *

op = OptParser()
scenario_common.prepare_option_parser_mode_flags(op)
op["workload1"] = PositionalArg()
op["workload2"] = PositionalArg()
op["timeout"] = IntFlag("--timeout", 600)
opts = op.parse(sys.argv)

with driver.Metacluster() as metacluster:
    cluster = driver.Cluster(metacluster)
    executable_path, command_prefix, serve_options = scenario_common.parse_mode_flags(opts)

    print "Starting cluster..."
    files1 = driver.Files(metacluster, db_path = "db-first", executable_path = executable_path, command_prefix = command_prefix)
    process1 = driver.Process(cluster, files1, log_path = "serve-output-first",
        executable_path = executable_path, command_prefix = command_prefix, extra_options = serve_options)
    process1.wait_until_started_up()

    print "Creating namespace..."
    http1 = http_admin.ClusterAccess([("localhost", process1.http_port)])
    dc = http1.add_datacenter()
    http1.move_server_to_datacenter(files1.machine_name, dc)
    ns = http1.add_namespace(protocol = "memcached", primary = dc)
    http1.wait_until_blueprint_satisfied(ns)

    host, port = driver.get_namespace_host(ns.port, [process1])
    workload_runner.run(opts["workload1"], host, port, opts["timeout"])

    print "Bringing up new server..."
    files2 = driver.Files(metacluster, db_path = "db-second", executable_path = executable_path, command_prefix = command_prefix)
    process2 = driver.Process(cluster, files2, log_path = "serve-output-second",
        executable_path = executable_path, command_prefix = command_prefix, extra_options = serve_options)
    process2.wait_until_started_up()
    http1.update_cluster_data(3)
    http1.move_server_to_datacenter(files2.machine_name, dc)
    http1.set_namespace_affinities(ns, {dc: 1})
    http1.check_no_issues()

    print "Waiting for backfill..."
    backfill_start_time = time.time()
    http1.wait_until_blueprint_satisfied(ns, timeout = 3600)
    print "Backfill completed after %d seconds." % (time.time() - backfill_start_time)

    print "Shutting down old server..."
    process1.check_and_stop()
    http2 = http_admin.ClusterAccess([("localhost", process2.http_port)])
    http2.declare_machine_dead(files1.machine_name)
    http2.set_namespace_affinities(ns.name, {dc.name: 0})
    http2.check_no_issues()
    http2.wait_until_blueprint_satisfied(ns.name)

    host, port = driver.get_namespace_host(http2.find_namespace(ns.name).port, [process2])
    workload_runner.run(opts["workload2"], host, port, opts["timeout"])

    cluster.check_and_stop()
