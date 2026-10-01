#include <stdbool.h>
#include <stdint.h>

#define MCDC_RET_IF (0x0001)
#define MCDC_RET_ELSE (0x0002)

uint32_t mcdc_check(bool a, bool b, bool c) {
    uint32_t retval;

    if ((a || b) && c) {
        retval = MCDC_RET_IF;
    } else {
        retval = MCDC_RET_ELSE;
    }

    return retval;
}

int main(void) {
    /* These calls take every branch outcome, but 'b == true' never
       independently determines the result, so a condition stays uncovered. */
    volatile uint32_t result = 0;

    result += mcdc_check(true, true, true);
    result += mcdc_check(false, false, false);
    result += mcdc_check(false, true, false);

    return 0;
}
