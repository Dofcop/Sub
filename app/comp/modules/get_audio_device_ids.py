import speech_recognition as sr

if __name__ == '__main__':
    list_mic = sr.Microphone.list_microphone_names()
    for i in range(0, len(list_mic)):
        print(i, list_mic[i].encode('cp1251').decode('utf-8'))
