#include "update-data.h"

int update_data()
{
	return called_from_update_data() + called_from_both(1);
}
