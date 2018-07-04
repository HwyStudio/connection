import serial
from serial.tools import list_ports
from threading import Thread, Lock
import traceback
import time
import socket
import copy

mutex = Lock()

# tp温度,0代表关，1代表开
# motor_forward电机正转，1表示正转，0无意义
#motor_reversal电机反转，1表示反转，0无意义
# motor_forward与motor_reversal不可同时为1
# og氧气，0代表关，1代表开
# pwm占空比，范围0-100
# code = [
# 	['tp', '1'.encode('utf-8')],
# 	['motor_forward', '0'.encode('utf-8')],
# 	['motor_reversal', '0'.encode('utf-8')],
# 	['og', '0'.encode('utf-8')],
# 	['pwm', '0'.encode('utf-8')]
# ]

data_rec = ''
data_rec = data_rec.encode('utf-8') # 由于串口使用的是字节，故而要进行转码，否则串口会不识别
temp = '0'


# 串口数据接收、套接字发送线程
def port_socket(port, client):
	global data_rec, temp
	while True:
		mutex.acquire()
		length = port.inWaiting()
		if length:
			data_rec += port.read(length).strip()
			print('****')
		# 获取还没接收到的数据长度
		length_test = port.inWaiting()
		# 判断是否已经将下位机传输过来的数据全部提取完毕，防止之前没有获取全部数据
		if len(data_rec) > 0 and length_test == 0:
			# print(data_rec)
			try:
				data = data_rec.decode('utf-8')
				temp = data[12:13]
				print('状态信息:', data[1:12])
				if temp == '1':
					client.sendall(data[1:12].encode('utf-8'))
				data_rec = ''
				data_rec = data_rec.encode('utf-8')
			except:
				traceback.print_exc()
				data_rec = ''
				data_rec = data_rec.encode('utf-8')
		mutex.release()
		time.sleep(0.1)


# 套接字接收、串口数据发送线程
def socket_port(port, client):
	global temp
	value = ''
	data = ''
	while True:
		mutex.acquire()
		try:
			value += client.recv(1024).decode('utf-8')
			data = copy.deepcopy(value)
		except:
			pass
		finally:
			if len(data) == 11 and temp == '0':
				print('控制信息', data)
				# print(value[0:3])
				port.write('S'.encode('utf-8'))
				time.sleep(0.1)
				for i in value:
					port.write(i.encode('utf-8'))
					time.sleep(0.1)
					print(i)
				port.write('e'.encode('utf-8'))
			elif temp == '1':
				print('接受成功')
				value = ''
		mutex.release()
		time.sleep(0.5)


def main():
	plist = list(list_ports.comports())
	plist_0 = list(plist[0])
	serial_port = plist_0[0]
	print(serial_port)
	# 打开串口
	port = serial.Serial(
		port = serial_port, # 端口
		baudrate = 115200, # 波特率
		parity = 'N', # 奇偶校验
		stopbits = 1, # 停止位
		bytesize = 8,
		timeout = 1
	)
	# socket.AF_INET用于服务器与服务器之间的网络通信
	# socket.SOCK_STREAM代表基于TCP的流式socket通信
	# 创建套接字
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# 需要连接的服务器地址
	address = ('120.79.145.37', 8889)
	try:
		# 连接服务器
		client.connect(address)
		# 套接字不阻塞
		client.setblocking(False)
	except:
		traceback.print_exc()
	# 串口同通信、套接字通信
	tr = Thread(target=port_socket, args=(port, client))
	ts = Thread(target=socket_port, args=(port, client))
	tr.start()
	ts.start()
	tr.join()
	ts.join()
	
	
if __name__ == '__main__':
	main()