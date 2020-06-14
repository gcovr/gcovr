#include <stdexcept>

int function_that_may_throw(bool die) {
    if (die) {
        throw std::runtime_error("the error");
    } else {
        return 42;
    }
}

struct RAII {
    bool die;

    RAII(bool);
    ~RAII();
    int method_that_may_throw() const {
        return function_that_may_throw(die);
    }
};

RAII::RAII(bool die) :die(die) {}
RAII::~RAII() {}

int function_with_catchers(int argc) {
    bool die_again = true;

    try {
        function_that_may_throw(argc == 1);
    } catch (std::exception&) {
        die_again = false;
    }

    // GCOV_EXCL_START
    RAII raii(die_again);
    // GCOV_EXCL_STOP

    try {
        raii.method_that_may_throw();
    } catch (std::exception&) {
        return 1;
    }

    function_that_may_throw(argc != 1);

    return 0;
}


int main(int argc, char* argv[]) {
    return function_with_catchers(argc);
}
