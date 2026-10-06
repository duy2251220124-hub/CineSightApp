import os

path = r'lib\screens\cs_login_screen.dart'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# We know the specific strings:
text = text.replace('Nh\xc3\xa2n vi\xc3\xaan r\xe1\xba\xa1p chi\xe1\xba\xbfu phim CineSight', 'Nhân viên rạp chiếu phim CineSight')
text = text.replace('M\xc3\xa3 nh\xc3\xa2n vi\xc3\xaan / Username', 'Mã nhân viên / Username')
text = text.replace('Qu\xc3\xaan m\xe1\xba\xadt kh\xe1\xba\xa9u?', 'Quên mật khẩu?')
text = text.replace('${CSMockData.employeeRole} \xc2\xb7 ${CSMockData.employeeId}', '${CSMockData.employeeRole} · ${CSMockData.employeeId}')
text = text.replace('M\xe1\xba\xadt kh\xe1\xba\xa9u / Password', 'Mật khẩu / Password')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Fixed cs_login_screen.dart')
