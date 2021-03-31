import sys
import pickle
import argparse
import encoder


def get_bytes(file: str) -> bytes:
    model: bytes = pickle.dumps(dict(zip(encoder.lowers, 26 * [0])))
    try:
        with open(file, mode='br') as f:
            model = f.read()
    except FileNotFoundError:
        print("The model file with such a name doesn't exist.")
    except pickle.UnpicklingError:
        print("The model file is incorrect.")
    finally:
        return model


def get_text(file: str) -> str:
    text: str = ''
    if file:  # проверяю хочет ли пользователь вносить из консоли или файла
        try:
            with open(file, mode='r') as f:
                text = f.read()
        except FileNotFoundError:
            print("The input or text file with such a name doesn't exist.")
            sys.exit()
    else:
        text = input()
    return text


def record(args_: argparse.Namespace) -> encoder.Any:
    """записывает нужные аргументы 
       и доставляет их в конструктор,
       генерируя нужный объект"""

    if args_.task in {'encode', 'decode'}:
        return encoder.ciphers[args_.cipher](get_text(args_.input_file))
    elif args_.task == 'train' and args_.cipher == 'caesar':
        return encoder.Caesar(get_text(args_.text_file))
    elif args_.task == 'hack' and args_.cipher in {'caesar', 'vigenere'}:
        return encoder.ciphers[args_.cipher](get_text(args_.input_file))
    else:
        print("Incorrect combination of cipher and task.")
        return encoder.ciphers[args_.cipher]('')


def output(text: encoder.Any, file: str) -> None:
    """выводит получившийся текст либо в консоль, либо в файл"""
    
    try:
        if file and isinstance(text, str):
            with open(file, mode='w') as f:
                f.write(text)
        elif isinstance(text, bytes):
            with open(file, mode='bw') as f:
                f.write(text)
        else:
            print(text)
    except FileNotFoundError:
        print("Model file with such a name doesn't exist.")


def commit(msg: encoder.Any, arguments: argparse.Namespace) -> None:
    """совершает нужное, в зависимости от задачи, действие и
	   сразу вызывает output (то есть выводит)"""

    try:
        if arguments.task in 'encode':
            output(msg.encode(arguments.key), arguments.output_file)
        elif arguments.task == 'decode':
            output(msg.decode(arguments.key), arguments.output_file)
        elif arguments.task == 'train':
            output(msg.train(), arguments.model_file)
        elif arguments.task == 'hack' and arguments.cipher == 'caesar':
            frequency = pickle.loads(get_bytes(arguments.model_file))
            if isinstance(frequency, dict):
                output(msg.hack(frequency), arguments.output_file)
            else:
                print("Incorrect model file.")
                sys.exit()
        elif arguments.task == 'hack':
            output(msg.hack(), arguments.output_file)
        else:
            print("Incorrect task.")  # не нужен выход
    except AttributeError:
        print("Incorrect task.")
        sys.exit()


def main():
    parser: argparse.ArgumentParser = \
        argparse.ArgumentParser(description = "Encodes text, decodes it with"
                                              " Caesar, Vigenere and Vernam"
                                              " ciphers. Hacks text encoded"
                                              " with Caesar-Vigenere ciphers")
    parser.add_argument("task", help="task the program need to carry out")
    parser.add_argument("--cipher", help="type of cipher", default="caesar")
    parser.add_argument("--key", help="keyword or number")
    parser.add_argument("--input-file", help="way to the input file", default='')
    parser.add_argument("--output-file", help="way to the out file", default='')
    parser.add_argument("--text-file", help="input for model", default='')
    parser.add_argument("--model-file", help="model for hacking", default='')

    args: argparse.Namespace = parser.parse_args()

    if args.cipher not in {'caesar', 'vigenere', 'vernam'}:
        print("Cipher is incorrect.")
    else:
        message: encoder.Any = record(args)
        commit(message, args)


if __name__ == '__main__':
    main()
