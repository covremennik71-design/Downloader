import unittest
from url_utils import normalize_youtube_url
class URLTests(unittest.TestCase):
 def test_bare_domain_gets_https(self): self.assertEqual(normalize_youtube_url("youtu.be/abcdefghijk"),"https://youtu.be/abcdefghijk")
 def test_https_is_preserved(self): self.assertEqual(normalize_youtube_url("https://youtube.com/watch?v=abcdefghijk"),"https://youtube.com/watch?v=abcdefghijk")
 def test_supported_paths(self):
  for p in ("embed","shorts","live","v"): self.assertEqual(normalize_youtube_url(f"youtube.com/{p}/abcdefghijk"),f"https://youtube.com/{p}/abcdefghijk")
 def test_rejects_unsupported_schemes_and_hosts(self):
  for u in ("ftp://youtube.com/watch?v=abcdefghijk","javascript:alert(1)","https://youtube.com.evil.test/watch?v=abcdefghijk","https://notyoutube.com/watch?v=abcdefghijk"):
   with self.assertRaises(ValueError): normalize_youtube_url(u)
 def test_rejects_invalid_ids(self):
  for u in ("https://youtube.com/","https://youtube.com/watch?v=short"):
   with self.assertRaises(ValueError): normalize_youtube_url(u)
if __name__=="__main__": unittest.main()
