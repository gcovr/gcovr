bool no(bool);
int yes(int);

int main(int argc, char *argv[])
{
   if (no(true)) {
      return yes(7);
   }
   else {
      return yes(10);
   }
}
