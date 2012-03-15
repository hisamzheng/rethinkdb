#ifndef CONTAINERS_CLONE_PTR_HPP_
#define CONTAINERS_CLONE_PTR_HPP_

#include "errors.hpp"
#include <boost/serialization/split_member.hpp>

/* `clone_ptr_t` is a smart pointer that calls the `clone()` method on its
underlying object whenever the `clone_ptr_t`'s copy constructor is called. It's
primarily useful when you have a type that effectively acts like a piece of
data (i.e. it can be meaningfully copied) but it also has virtual methods.
Remember to declare `clone()` as a virtual method! */

template<class T>
class clone_ptr_t {
public:
    clone_ptr_t() THROWS_NOTHING;
    ~clone_ptr_t() THROWS_NOTHING;

    /* Takes ownership of the argument. */
    explicit clone_ptr_t(T *) THROWS_NOTHING;

    clone_ptr_t(const clone_ptr_t &x) THROWS_NOTHING;
    template<class U>
    clone_ptr_t(const clone_ptr_t<U> &x) THROWS_NOTHING;  // NOLINT(runtime/explicit)

    clone_ptr_t &operator=(const clone_ptr_t &x) THROWS_NOTHING;
    template<class U>
    clone_ptr_t &operator=(const clone_ptr_t<U> &x) THROWS_NOTHING;

    T &operator*() const THROWS_NOTHING;
    T *operator->() const THROWS_NOTHING;
    T *get() const THROWS_NOTHING;

    /* This mess is so that we can use `clone_ptr_t` in boolean contexts. */
    typedef void (clone_ptr_t::*booleanish_t)();
    operator booleanish_t() const THROWS_NOTHING;

private:
    template<class U> friend class clone_ptr_t;
    friend class boost::serialization::access;

    void truth_value_method_for_use_in_boolean_conversions();

    template<class Archive>
    void save(Archive & ar, UNUSED const unsigned int version) const {
        ar & object;
    }
    template<class Archive>
    void load(Archive & ar, UNUSED const unsigned int version) {
        if (object) {
            delete object;
            object = NULL;
        }
        ar & object;
    }
    BOOST_SERIALIZATION_SPLIT_MEMBER()

    T *object;
};

#include "containers/clone_ptr.tcc"

#endif /* CONTAINERS_CLONE_PTR_HPP_ */
