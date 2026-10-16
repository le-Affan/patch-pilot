"""Built-in buggy programs plus pre-recorded fixes for offline replay."""

SAMPLES = {
    "Off-by-one (sum of list)": {
        "code": '''def total(nums):
    s = 0
    for i in range(len(nums) + 1):
        s += nums[i]
    return s

print(total([1, 2, 3, 4]))
''',
        "diagnosis": "range(len(nums) + 1) iterates one index past the end, raising IndexError. Iterate exactly len(nums) items.",
        "fixed_code": '''def total(nums):
    s = 0
    for i in range(len(nums)):
        s += nums[i]
    return s

print(total([1, 2, 3, 4]))
''',
    },
    "KeyError (word counter)": {
        "code": '''def count_words(text):
    counts = {}
    for w in text.lower().split():
        counts[w] += 1
    return counts

print(count_words("the cat and the hat"))
''',
        "diagnosis": "counts[w] += 1 reads a key that does not exist yet, raising KeyError. Use counts.get(w, 0) + 1.",
        "fixed_code": '''def count_words(text):
    counts = {}
    for w in text.lower().split():
        counts[w] = counts.get(w, 0) + 1
    return counts

print(count_words("the cat and the hat"))
''',
    },
    "Bad recursion base case (factorial)": {
        "code": '''def factorial(n):
    if n == 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
print(factorial(0))
''',
        "diagnosis": "Base case only handles n == 1, so factorial(0) recurses forever into negatives (RecursionError). Use n <= 1.",
        "fixed_code": '''def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
print(factorial(0))
''',
    },
    "Failing assert test (is_palindrome)": {
        "code": '''def is_palindrome(s):
    cleaned = [c for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]

assert is_palindrome("racecar")
assert is_palindrome("A man, a plan, a canal: Panama")
assert not is_palindrome("hello")
print("all tests passed")
''',
        "diagnosis": "Comparison is case-sensitive, so 'A man, a plan...' fails ('A' != 'a'). Lowercase characters while cleaning.",
        "fixed_code": '''def is_palindrome(s):
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]

assert is_palindrome("racecar")
assert is_palindrome("A man, a plan, a canal: Panama")
assert not is_palindrome("hello")
print("all tests passed")
''',
    },
}


def recorded_fixer_for(code: str):
    """Return a fixer replaying the recorded fix if `code` matches a sample, else None."""
    for s in SAMPLES.values():
        if s["code"].strip() == code.strip():
            def fixer(_code, _output, _history, s=s):
                return {"diagnosis": s["diagnosis"], "fixed_code": s["fixed_code"]}
            return fixer
    return None
