#!/usr/bin/python

banner = """
VPNbook Python commandline VPN Client
"""

log_dir = '/var/log/anonimato/'
default_logfile = 'log_anon.log'
openvpn_logfile = 'log_anon_openvpn.log'
exception_logfile = 'log_anon_exception.log'
loop = 1

try:
	import sys, urllib2, re, time, subprocess
	import pexpect, zipfile, shutil, os

except ImportError as e:
	msg = '[-] An ImportError has occurred. Please review the \'' + exception_logfile + '\' for details.'
	print(msg)
	try:
		if not os.path.exists(log_dir):
			os.makedirs(log_dir)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise
		sys.exit(1)
	with open(os.path.join(log_dir, default_logfile), 'a') as logfile:
		logfile.write(msg + '\n')
	with open(os.path.join(log_dir, exception_logfile), 'a') as elogfile:
		elogfile.write(str(e.args[0]))
	sys.exit(1)

def print_menu():
	#os.system('clear')

	print "Welcome,\n"
	print "Please choose the menu you want to start:"
	print "1. Download VPN config .ovpn files"
    	print "2. Connect to VPN"
    	print "\n3. Quit"

def log(msg, file_path=default_logfile):
	if not os.path.exists(log_dir):
		try:
			os.makedirs(log_dir)
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise
			sys.exit(1)
	with open(os.path.join(log_dir, file_path), 'a') as logfile:
		logfile.write(time.strftime('%Y-%m-%d, %H:%M:%S') + ' | ' + msg + '\n')

def backup_file(file_path):
	if os.path.isfile(file_path):
		try:
			shutil.copy2(file_path, file_path + '.original')
			log('Backup of ' + file_path + ' successful')
		except:
			log('Error taking backup of file ' + file_path)
			raise
	else:
		log('File ' + file_path + ' not found, therefore no backup was created')

def restore_file(file_path):
	if os.path.isfile(file_path + '.original'):
		try:
			shutil.copy2(file_path + '.original', file_path)
			log('Backup of ' + file_path + ' restored successfully')
			os.remove(file_path + '.original')
			log('Backup of ' + file_path + ' was removed')
		except:
			log('Error restoring original file from backup')
			raise
	else:
		log('No backup of file ' + file_path + ' was found')

def write_resolvconf(file_path):
	print '\n[+] Writing Resolv.conf'
	with open(file_path, 'w') as conf:
		conf.write('nameserver 8.8.8.8')
	print '\t - Done'

def unzip_file(zip_file,extract_path):
	print '\n[+] Unzipping file'
	if not os.path.exists(extract_path):
                try:
                        os.makedirs(extract_path)
                except OSError as e:
                        if e.errno != errno.EEXIST:
                                raise
                        sys.exit(1)
	try:
		zip_ref = zipfile.ZipFile(extract_path+zip_file, 'r')
        	zip_ref.extractall(extract_path)
        	zip_ref.close()
		print '\t Done\n'
	except:
		print 'Unzip error\n'


#Funcion que obtiene las credenciales de la vpn
def vpnGetCreds():
	username='vpnbook'
	response = urllib2.urlopen('http://www.vpnbook.com/freevpn')
	lines = response.readlines()
	r = re.compile(r'Password')
	for i in range(len(lines)):
		if r.search(lines[i]):
			password = lines[i].strip()
			password = password.split(':')[1]
			password = password.split('>')[1]
			password = password.split('<')[0]
			break
	return username,password

#Funcion que obtiene los archivos de la vpn
def vpn_get_config_file(url,zip_file):
	save_path = '/etc/openvpn/profiles/'
	if not os.path.exists(save_path):
                try:
                        os.makedirs(save_path)
                except OSError as e:
                        if e.errno != errno.EEXIST:
                                raise
                        sys.exit(1)
	now=time.time()
	download=urllib2.urlopen(url)
	save_zip_file = save_path + zip_file
	f=open(save_zip_file,'w')
	f.write(download.read())
	f.close()
	elapsed = time.time() - now
	print 'Descargado el archivo: %s en %0.3fs' % (zip_file,elapsed)
	unzip_file(zip_file, save_path)

#Funcion que realiza la conexion a la vpn
def vpn_connect():
	print banner
	log('**** Script started *****')

	backup_file('/etc/resolv.conf')
	write_resolvconf('/etc/resolv.conf')

	print '\n[+] Connecting to VPNBook...'
	user,password = vpnGetCreds()
	configFile = subprocess.check_output('ls /etc/openvpn/profiles/*.ovpn | shuf -n 1', shell=True)
	try:
		execute=pexpect.spawn('openvpn '+configFile, echo=False, logfile=open(os.path.join(log_dir, openvpn_logfile), 'ab'))
		execute.expect('Enter Auth Username:')
		execute.sendline(user)
		execute.expect('Enter Auth Password:')
		execute.sendline(password)
		execute.expect('Initialization Sequence Completed')
		print '\t - Done'

		print '\n[+] Connected - press Ctrl-C to exit client.'
		execute.interact(output_filter=lambda _: '')

		raise KeyboardInterrupt

	except KeyboardInterrupt:
		print '\n[-] Exiting VPN script'
		log('**** Quit by keyboard interrupt ****')

	except pexpect.EOF as e:
		msg = '[-] An EOF exception occurred while spawning the OpenVPN instance.\nUsually this occurs due to a wrong or missing path to the certificate file.\nThe full error was logged in \'' + exception_logfile + '\' for further inspection.'
		print '\n' + msg
		log(msg)
		log(e.args[0], exception_logfile)

	except pexpect.TIMEOUT as e:
		msg = '[-] A TIMEOUT exception occurred. Read time exceeded its limit.i\nFull error was logged in \'' + exception_logfile + '\' for further inspection.'
		print '\n' + msg
		log(msg)
		log(e.args[0], exception_logfile)

if __name__ == "__main__":

	try:
		if os.geteuid() != 0:
			print('This script must be run with root privileges.\n')
			sys.exit(1)
		else:
			while loop:
				print_menu()
				choice_valid= 0
				while not choice_valid:
					try:
						choice = int(raw_input('Enter your choice [1-3]: '))
						choice_valid=1
					except ValueError, e :
						print "'%s' is not a valid integer." % e.args[0].split(": ")[1]

				if choice == 1:
					url = 'http://www.vpnbook.com/free-openvpn-account/VPNBook.com-OpenVPN-Euro1.zip'
					zip_file = 'vpn.zip'
					vpn_get_config_file(url, zip_file)
				elif choice ==2:
					vpn_connect()
				elif choice ==3:
					loop = False
				else:
					print '\nNot a valid choice'

	except:
		msg = '[-] An unhandled exception occurred, and can be found in \'' + exception_logfile + '\''
		print('\n' + msg)
		log(msg)
		log(str(sys.exc_info()), exception_logfile)

	finally:
		restore_file('/etc/resolv.conf')
		log('**** Script gracefully ended ****')

