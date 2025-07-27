from obfuskey.alphabets import CROCKFORD_BASE32, BASE64_URL_SAFE

test_string_crockford = CROCKFORD_BASE32
print(f"Length of Crockford: {len(test_string_crockford)}")
print(f"Length of set of Crockford: {len(set(test_string_crockford))}")
print(f"Has duplicates? {len(set(test_string_crockford)) != len(test_string_crockford)}")

test_string_base64url = BASE64_URL_SAFE
print(f"Length of Base64 URL: {len(test_string_base64url)}")
print(f"Length of set of Base64 URL: {len(set(test_string_base64url))}")
print(f"Has duplicates? {len(set(test_string_base64url)) != len(test_string_base64url)}")