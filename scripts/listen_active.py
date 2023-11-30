import sys
import os
import time


def out_read(file) -> str:
    with open(file, "r") as f:
        return f.read()


def get_new(str1, str2) -> str:
    return str2[len(str1) :]


def main():
    # Fetch repo dir
    this_dir = os.path.abspath(os.path.dirname(__file__))

    # Fetch outputfile
    out_file = os.path.join(this_dir, "nohup.out")

    # Display output file
    print(f"---- Showing output ----\n")

    prev = ""

    try:
        while True:
            time.sleep(0.1)
            new = get_new(prev, out_read(out_file))

            if new == "":
                continue

            print("\n", new, end="")
            prev += new
    except KeyboardInterrupt:
        print()
        exit()


if __name__ == "__main__":
    main()
