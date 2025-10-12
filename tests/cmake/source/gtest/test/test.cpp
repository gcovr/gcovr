#include <gtest/gtest.h>

#include "../source/code.hpp"

TEST(HelloTest, TestFoo1) {
  EXPECT_EQ(foo1(-1), 1);
  EXPECT_EQ(foo1(0), 0);
  EXPECT_EQ(foo1(1), 1);
}

TEST(HelloTest, TestFoo2) {
  EXPECT_EQ(foo2(-1), 1);
  // EXPECT_EQ(foo2(0), 0);
  EXPECT_EQ(foo2(1), 1);
}

int main(int argc, char** argv)
{
	testing::InitGoogleTest(&argc, argv);
	return RUN_ALL_TESTS();
}
