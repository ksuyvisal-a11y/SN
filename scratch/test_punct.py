import re

def test_fix(res):
    # Strip any trailing junk words like 'ចាន'
    res = re.sub(r'\s*ចាន[។.!?]*$', '!', res)
    # Clean double punctuation only if ? or ! is actually present!
    if '?' in res or '!' in res:
        res = re.sub(r'[?!]+[។.\s]*$', '?!', res)
    res = re.sub(r'([។.!?])\1+', r'\1', res)
    
    if re.search(r'ខ្ញុំ.*(?:ចៅហ្វាយ|ថៅកែ)', res):
        return 'ខ្ញុំនេះទើបជាថៅកែពិតប្រាកដ!'
    if re.search(r'ខ្ញុំ.*ដឹង', res):
        return 'ខ្ញុំដឹងតាំងពីដំបូងមកម្ល៉េះ!'
    return res

print(test_fix('ខ្ញុំជាចៅហ្វាយពិតប្រាកដ! ចាន'))
print(test_fix('ខ្ញុំ​ដឹង​ហើយ'))
print(test_fix('មិនអីទេ'))
print(test_fix('តើអ្នកទៅណា?'))
