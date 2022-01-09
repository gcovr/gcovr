#include "stdint.h"
#include "stdbool.h"

bool checkBiggerTrue(int a)
{
   if (a > 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkBiggerFalse(int a)
{
   if (a > 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkBiggerBoth(int a)
{
   if (a > 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkSmallerTrue(int a)
{
   if (a < 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkSmallerFalse(int a)
{
   if (a < 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkEqualTrue(int a)
{
   if (a == 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkEqualFalse(int a)
{
   if (a == 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkNotEqualTrue(int a)
{
   if (a != 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkNotEqualFalse(int a)
{
   if (a != 5)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkComplexTrue(int a)
{
   if (a == 5 || (a > 5 && a < 10))
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkComplexFalse(int a)
{
   if (a == 5 || (a > 5 && a < 10))
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkElseIf1(int a)
{
   if (a == 5)
   {
      return true;
   }
   else if (a == 9)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkElseIf2(int a)
{
   if (a == 5)
   {
      return true;
   }
   else if (a == 10)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkElseIf3(int a)
{
   if (a == 5)
   {
      return true;
   }
   else if (a == 10)
   {
      return true;
   }
   else
   {
      return false;
   }
}

bool checkSwitch1(int a)
{
   switch (a)
   {
   case 5: return true; break;
   case 10:
      return true;
      break;
   default:
      return false;
      break;
   }
}

bool checkSwitch2(int a)
{
   switch (a)
   {
   case 5:
      return true;
      break;
   case 10:
      return true;
      break;
   default:
      return false;
      break;
   }
}

bool checkSwitch3(int a)
{
   switch (a)
   {
   case 5:
      return true;
      break;
   case 10:
      return true;
      break;
   default:
      return false;
      break;
   }
}

bool checkCompactBranch1True(int a)
{
   if (a > 5) { return true; } else { return false; }
}

bool checkCompactBranch1False(int a)
{
   if (a > 5) { return true; } else { return false; }
}

bool checkCompactBranch2True(int a)
{
   if (a > 5 && a < 10) { return true; } else { return false; }
}

bool checkCompactBranch2False(int a)
{
   if (a > 5 && a < 10) { return true; } else { return false; }
}

bool checkTernary1True(int a)
{
   return (a == 5) ? true : false;
}

bool checkTernary1False(int a)
{
   return (a == 5) ? true : false;
}

bool checkTernary2True(int a)
{
   return (a > 5 && a < 10) ? true : false;
}

bool checkTernary2False(int a)
{
   return (a > 5 && a < 10) ? true : false;
}

int checkForLoop(int a)
{
   int temp = 0;
   for (int i = 0; i < a; i++)
   {
      temp += a;
   }
   return temp;
}

int checkComplexForLoop(int a)
{
   int temp = 0;
   for (int i = 0; i < a && a < 6; i++)
   {
      temp += a;
   }
   return temp;
}

int checkWhileLoop(int a)
{
   int temp = 0;
   int counter = 0;

   while (counter < a)
   {
      counter++;
      temp += a;
   }

   return temp;
}

int checkDoWhileLoop(int a)
{
   int temp = 0;
   int counter = 0;

   do
   {
      counter++;
      temp += a;
   } while (counter < a);

   return temp;
}

bool checkInterpreter(int a)
{
   char test1[] = " while ";
   a++;

   char test2[] = " for ";
   {
      a++;
   }

   char test3[] = " if(";
   a++;

   char test4[] = " do ";
   a++;

   if (a > 5)
   {
      return true;
   }

   return false;
}

int main(int argc, char *argv[])
{
   checkBiggerTrue(6);
   checkBiggerFalse(4);
   checkBiggerBoth(6);
   checkBiggerBoth(4);

   checkSmallerTrue(4);
   checkSmallerFalse(6);

   checkEqualTrue(5);
   checkEqualFalse(2);

   checkNotEqualTrue(2);
   checkNotEqualFalse(5);

   checkComplexTrue(8);
   checkComplexFalse(2);

   checkElseIf1(5);
   checkElseIf2(10);
   checkElseIf3(0);

   checkSwitch1(5);
   checkSwitch2(10);
   checkSwitch3(0);

   checkCompactBranch1True(6);
   checkCompactBranch1False(4);

   checkCompactBranch2True(6);
   checkCompactBranch2False(4);

   checkTernary1True(6);
   checkTernary1False(4);

   checkTernary2True(6);
   checkTernary2False(4);

   checkForLoop(5);
   checkComplexForLoop(5);
   checkWhileLoop(5);
   checkDoWhileLoop(5);

   checkInterpreter(2);

   return 0;
}
