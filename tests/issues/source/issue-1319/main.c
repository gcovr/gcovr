/* t.c */

int __helper(int x)
{
	return x + 1;
}

int main(void)
{
	return __helper(-1);
}
