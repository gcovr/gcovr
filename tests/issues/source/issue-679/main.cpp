
void test(const bool b) {
  if (b) {
    for (int i = 0; i < 10; i++) {
    }
  }
}

int main(int argc, char *argv[])
{
   test(false);
   test(true);

   return 0;
}
