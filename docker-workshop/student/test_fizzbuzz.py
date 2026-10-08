import unittest
from fizzbuzz import fizzbuzz

class TestFizzBuzz(unittest.TestCase):
    def test_returns_string(self):
        for n in range(1, 21):
            self.assertIsInstance(fizzbuzz(n), str)

    def test_fizz(self):
        for n in [3, 6, 9, 12, 18, 21, 99]:
            with self.subTest(n=n):
                self.assertEqual(fizzbuzz(n), "Fizz")

    def test_buzz(self):
        for n in [5, 10, 20, 25, 35, 95]:
            with self.subTest(n=n):
                self.assertEqual(fizzbuzz(n), "Buzz")

    def test_fizzbuzz(self):
        for n in [15, 30, 45, 60, 75, 90]:
            with self.subTest(n=n):
                self.assertEqual(fizzbuzz(n), "FizzBuzz")

    def test_numbers(self):
        cases = {1: "1", 2: "2", 4: "4", 7: "7", 8: "8", 11: "11", 13: "13", 14: "14"}
        for n, expected in cases.items():
            with self.subTest(n=n):
                self.assertEqual(fizzbuzz(n), expected)

if __name__ == "__main__":
    unittest.main(verbosity=2)
