
#if (defined __GNUC__ && (__GNUC__ >= 6)) || (defined __clang_major__)
#include "switch_test.h"

SwitchTestIssue783::SwitchTestIssue783() : _name("test") {}

void SwitchTestIssue783::checkSwitch() {
    doSomething(EnumNamespace::EnumValue_1);
}
#endif
