import csv

emails = [
    'smartinez6461@gmail.com', 'ananya-nair@gmail.com', 's.yoon04@gmail.com',
    'almeida.mariana@gmail.com', 'amara-okeke@proton.me', 'k.appiah88@gmail.com',
    'mori.ren@gmail.com', 'akosua.gyasi@gmail.com', 'seoyeon-han@gmail.com',
    'thandiwe.m6866@zoho.com', 'noah.f438085@outlook.com', 'camille.bernard86@outlook.com',
    'addo.kofi@gmail.com'
]

with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['email'] in emails:
            print(row)
