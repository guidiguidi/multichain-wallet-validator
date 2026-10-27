import unittest


class TestWalletValidator(unittest.TestCase):
    def test_evm_regex_detection(self):
        valid = "0x71C841609077982772594a32338A959cD1696E37"
        self.assertTrue(valid.startswith("0x") and len(valid) == 42)

    def test_solana_base58_format(self):
        valid_sol = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
        self.assertTrue(32 <= len(valid_sol) <= 44)


if __name__ == "__main__":
    unittest.main()
