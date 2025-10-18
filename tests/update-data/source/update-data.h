#ifdef __cplusplus
extern "C" {
#endif

int update_data(void);

static int called_from_main(void)
{
	return 0;
}

static int called_from_update_data(void)
{
	return 1;
}

static int called_from_both(int which)
{
	if (which == 0) {
		return 1;
	}
	else {
		return 0;
	}
}

#ifdef __cplusplus
}
#endif
