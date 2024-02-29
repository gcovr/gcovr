#include "update-data.h"

int main(int argc, char* argv[])
{
	int main_value = called_from_main() + called_from_both(0);
	int ud_value = update_data();
	return main_value - ud_value;
}
