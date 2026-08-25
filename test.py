import pymupdf

pdf = pymupdf.open("books/doctor-bot-1-fixed.pdf")

print("Pages:", len(pdf))

for i in range(5):
    text = pdf[i].get_text()
    print(f"\nPAGE {i + 1}")
    print(repr(text[:500]))