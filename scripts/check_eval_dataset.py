import sys
from collections import Counter

from eval.dataset import DEV_PATH, TEST_PATH, EvalExample, check_dataset, load_examples


def print_summary(name: str, examples: list[EvalExample]) -> None:
    status_counts = Counter(example.label_status.value for example in examples)
    category_counts = Counter(example.category.value for example in examples)
    print(f"{name}: {len(examples)} examples, status {dict(status_counts)}")
    print(f"  categories {dict(category_counts)}")


def main() -> int:
    dev = load_examples(DEV_PATH)
    test = load_examples(TEST_PATH)
    print_summary("dev", dev)
    print_summary("test", test)
    tag_counts = Counter(tag.value for example in dev + test for tag in example.tags)
    print(f"tags {dict(sorted(tag_counts.items()))}")
    problems = check_dataset(dev, test)
    for problem in problems:
        print(f"PROBLEM: {problem}")
    if not problems:
        print("dataset OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
