
def hash_user(username, hash_key):
    p = hash_key
    n = 360
    hash_code = 0
    p_pow = 1
    for c in username:
        hash_code = (hash_code + (ord(c) - ord('A') + 1)*p_pow)%n
        p_pow = (p_pow*p)%n
    return hash_code

print(hash_user('INDIA', 419))
print(hash_user('RUSSIA', 757))
print(hash_user('CHINA', 271))
print(hash_user('GERMANY', 89))