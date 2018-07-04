from socket import *
from threading import Thread, Lock
import pymysql
import time

# 清空news表
sql_delete_news = "delete from news"
# 清空MyPara表
sql_delete_MyPara = "delete from MyPara"
# 增加
sql_insert = "insert into news(tp, dis, light, og, Feed) values(%s, %s, %s, %s, %s)"
# 查询MyPara表标志位，id
sql_check_id = "select id from MyPara order by id desc limit 1"
# 查询MyPara表数据位，Temp
sql_check_Temp = "select Temp from MyPara order by id desc limit 1"
# 查询MyPara表数据位，High
sql_check_High = "select High from MyPara order by id desc limit 1"
# 查询MyPara表数据位，Light
sql_check_Light = "select Light from MyPara order by id desc limit 1"
# 查询MyPara表数据位，ProOxy
sql_check_ProOxy = "select ProOxy from MyPara order by id desc limit 1"
# 查询MyPara表数据位，Water
sql_check_Water = "select Water from MyPara order by id desc limit 1"
# 查询MyPara表数据位，Food
sql_check_Food = "select Food from MyPara order by id desc limit 1"
# 创建锁
mutex = Lock()


# 1. 收数据，然后存至数据库
def recvData(client_socket, cursor, mysql_db):
	while True:
		recvInfo = client_socket.recv(1024).decode('utf-8')
		mutex.acquire()
		print('******')
		print(recvInfo)
		cursor.execute(sql_insert, [recvInfo[0:3], recvInfo[3:6], recvInfo[6:9], recvInfo[9:10], recvInfo[10:11]])
		mysql_db.commit()
		# cursor.execute(sql_insert, [recvInfo[3:6]])
		# mysql_db.commit()
		# cursor.execute(sql_insert, [recvInfo[6:9]])
		# mysql_db.commit()
		# cursor.execute(sql_insert, [recvInfo[9:10]])
		# mysql_db.commit()
		mutex.release()


# 2. 检测数据库，发数据
def sendData(client_socket, cursor, mysql_db):
	data_last = 0
	while True:
		#  锁定
		mutex.acquire()
		count = cursor.execute(sql_check_id)
		mysql_db.commit()
		if count == 1:
			data_now = cursor.fetchall()
			if data_last != data_now[0][0]:
				data_last = data_now[0][0]
				# 发送温度
				cursor.execute(sql_check_Temp)
				setting_Temp = str(int(cursor.fetchall()[0][0] * 10))
				print(setting_Temp)
				client_socket.sendall(setting_Temp.encode('utf-8'))
				# 发送高度
				cursor.execute(sql_check_High)
				setting_High = str(int(cursor.fetchall()[0][0] * 10))
				print(setting_High)
				client_socket.sendall(setting_High.encode('utf-8'))
				# 发送光照
				cursor.execute(sql_check_Light)
				setting_Light = str(int(cursor.fetchall()[0][0] * 10))
				print(setting_Light)
				client_socket.sendall(setting_Light.encode('utf-8'))
				# 发送氧气
				cursor.execute(sql_check_ProOxy)
				setting_ProOxy = str(cursor.fetchall()[0][0])
				print(setting_ProOxy)
				client_socket.sendall(setting_ProOxy.encode('utf-8'))
				# 发送喂食
				cursor.execute(sql_check_Food)
				setting_Food = str(cursor.fetchall()[0][0])
				print(setting_Food)
				client_socket.sendall(setting_Food.encode('utf-8'))
		mutex.release()
		time.sleep(1)


def main():
	global table_id
	# 创建连接通道, 设置连接ip, port, 用户, 密码以及所要连接的数据库
	mysql_db = pymysql.connect(
		host='localhost',
		port=3306,
		user='root',
		passwd='123456',
		db='UserSet'
	)
	# 创建游标, 操作数据库, 指定游标返回内容为字典类型
	cursor = mysql_db.cursor()
	# # 清空news表
	# cursor.execute(sql_delete_news)
	# mysql_db.commit()
	# # 清空MyPara表
	# cursor.execute(sql_delete_MyPara)
	# mysql_db.commit()
	
	# 创建socket
	tcpSerSocket = socket(AF_INET, SOCK_STREAM)
	tcpSerSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	# 绑定本地信息
	address = ('', 8889)
	tcpSerSocket.bind(address)
	# 使用socket创建的套接字默认的属性是主动的，使用listen将其变为被动的，这样就可以接收别人的链接了
	tcpSerSocket.listen(1024)
	
	# 如果有新的客户端来链接服务器，那么就产生一个新的套接字专门为这个客户端服务器
	while True:
		client_socket, client_address = tcpSerSocket.accept()
		print("[%s, %s]用户连接上了" % client_address)
		tr = Thread(target=recvData, args=(client_socket, cursor, mysql_db,))
		ts = Thread(target=sendData, args=(client_socket, cursor, mysql_db,))
		tr.start()
		ts.start()
		tr.join()
		ts.join()
	client_socket.close()
	tcpSerSocket.close()

if __name__ == '__main__':
	main()
