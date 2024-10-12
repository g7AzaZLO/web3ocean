from web3 import Web3, Account
import sys

# Подключение к узлу Oasis
chain_url = 'https://sapphire.oasis.io'
web3 = Web3(Web3.HTTPProvider(chain_url))

if not web3.is_connected():
    print("Не удалось подключиться к сети Oasis.")
    sys.exit()


def load_wallets() -> list[str]:
    """
    Читает приватные ключи из файла wallets.txt.

    Returns:
        list[str]: Список приватных ключей из файла.
    """
    with open('wallets.txt', 'r') as file:
        return [line.strip().split()[0] for line in file if line.strip()]


def save_wallet(private_key: str, public_key: str) -> None:
    """
    Сохраняет приватный и публичный ключи кошелька в файл wallets.txt.

    Args:
        private_key (str): Приватный ключ кошелька.
        public_key (str): Публичный адрес кошелька.
    """
    with open('wallets.txt', 'a') as file:
        # Проверка, не пустой ли файл, и добавление новой строки перед записью
        if file.tell() != 0:
            file.write("\n")
        file.write(f"{private_key} {public_key}")


def check_balances() -> None:
    """
    Проверяет и выводит баланс каждого кошелька, записанного в wallets.txt.
    Также выводит общую сумму средств на всех кошельках.
    """
    private_keys = load_wallets()
    total_balance = 0
    for pk in private_keys:
        account = web3.eth.account.from_key(pk)
        from_address = account.address
        balance = web3.eth.get_balance(from_address)

        if balance == 0:
            print(f"Адрес {from_address} имеет нулевой баланс. Пропускаем.")
        else:
            print(f"Баланс адреса {from_address}: {web3.from_wei(balance, 'ether')} ROSE")
            total_balance += balance

    print(f"Общая сумма на всех кошельках: {web3.from_wei(total_balance, 'ether')} ROSE")


def transfer_funds() -> None:
    """
    Переводит все доступные средства с каждого кошелька из wallets.txt
    на указанный адрес, после вычета комиссии за транзакцию.

    Запрашивает адрес назначения у пользователя и проверяет его на корректность.
    """
    private_keys = load_wallets()
    destination_address = input("Введите адрес кошелька для получения средств: ")

    if not web3.is_address(destination_address):
        print("Введен неверный адрес.")
        return

    for pk in private_keys:
        account = web3.eth.account.from_key(pk)
        from_address = account.address
        balance = web3.eth.get_balance(from_address)

        if balance == 0:
            print(f"Адрес {from_address} имеет нулевой баланс. Пропускаем.")
            continue

        gas_price = web3.eth.gas_price

        # Формируем временную транзакцию для оценки газа
        temp_tx = {
            'from': from_address,
            'to': destination_address,
            'value': balance,
        }

        try:
            # Оценка газ-лимита для транзакции
            gas_limit = web3.eth.estimate_gas(temp_tx)
        except Exception as e:
            print(f"Не удалось оценить газ для {from_address}: {e}")
            continue

        gas_cost = gas_price * gas_limit

        if balance <= gas_cost:
            print(f"Недостаточно средств на {from_address} для покрытия комиссии. Пропускаем.")
            continue

        value_to_send = balance - gas_cost
        tx = {
            'from': from_address,
            'to': destination_address,
            'value': value_to_send,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(from_address, 'pending'),
        }

        signed_tx = web3.eth.account.sign_transaction(tx, private_key=pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Транзакция отправлена с {from_address}. Хэш транзакции: {web3.to_hex(tx_hash)}")

    print("Все транзакции обработаны.")


def generate_wallets() -> None:
    """
    Генерирует указанное количество новых кошельков, выводит их информацию
    и сохраняет в файл wallets.txt.

    Запрашивает у пользователя количество кошельков для генерации.
    """
    nums = int(input("Введите количество кошельков для генерации: "))
    Account.enable_unaudited_hdwallet_features()

    for i in range(nums):
        print("------------------------------")
        account, mnemonic = Account.create_with_mnemonic()
        print(f"Адрес вашего кошелька: {account.address}")
        print(f"Сид фраза вашего кошелька: {mnemonic}")
        print(f"Приватный ключ вашего кошелька: {account.key.hex()}")

        save_wallet(account.key.hex(), account.address)


def menu() -> None:
    """
    Меню выбора действий. Позволяет пользователю выбирать между проверкой балансов,
    переводом средств и генерацией новых кошельков.
    """
    while True:
        print("\nВыберите действие:")
        print("1. Проверить баланс кошельков")
        print("2. Перевести средства на указанный адрес")
        print("3. Сгенерировать новые кошельки")
        print("0. Выход")

        choice = input("Ваш выбор: ")
        if choice == '1':
            check_balances()
        elif choice == '2':
            transfer_funds()
        elif choice == '3':
            generate_wallets()
        elif choice == '0':
            print("Выход из программы.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    menu()
