#pragma once

#include <cstdint>
#include <string>

namespace EnumNamespace {
    enum SomeEnum {
        EnumValue_1,
        EnumValue_2,
        EnumValue_3,
    };
}

struct SwitchTestIssue783 {
    SwitchTestIssue783();

    static double doSomething(EnumNamespace::SomeEnum value) {
        switch (value) {
            case EnumNamespace::EnumValue_1: return 50.0;
            case EnumNamespace::EnumValue_2: return 100.0;
            case EnumNamespace::EnumValue_3: return 25.0;
        }
        return 0.0;
    }

    void checkSwitch();
private:
    std::string _name;
};
