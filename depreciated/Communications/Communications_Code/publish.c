#include <unistd.h>
#include <zcm/zcm.h>
#include <sensor_info_t.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <termios.h>
#include <fcntl.h>
#include <string.h>

int main(int argc, char *argv[])
{
	zcm_t *zcm = zcm_create("udpm://234.255.76.67:7667?ttl=1");
	int fd, dl;
	int stop = 0;
	// system( "MODE /dev/ttyACM0: BAUD=9600 PARITY=n DATA=8 STOP=1" );
	fd = open("/dev/ttyACM0", O_RDWR | O_NOCTTY);
	dl = open("/dev/ttyACM1", O_RDWR | O_NOCTTY);
	char buf[256];
	char buf2[256];
	// char accx[256];
	// char accy[256];
	// char accz[256];
	char accel[256];
	char gyro[256];
	char mag[256];
	char press[256];
	char prox[256];
	// char dist[256];
	char s_dist[256];
	char l_dist[256];

	// int n = read(serialPort, &buf, 128);
	sensor_info_t msg;
	// printf("%s\n",buf);
	struct termios toptions;

	/* Get currently set options for the tty */
	tcgetattr(fd, &toptions);

	/* Set custom options */

	/* 9600 baud */
	cfsetispeed(&toptions, B9600);
	cfsetospeed(&toptions, B9600);
	/* 8 bits, no parity, no stop bits */
	toptions.c_cflag &= ~PARENB;
	toptions.c_cflag &= ~CSTOPB;
	toptions.c_cflag &= ~CSIZE;
	toptions.c_cflag |= CS8;
	/* no hardware flow control */
	toptions.c_cflag &= ~CRTSCTS;
	/* enable receiver, ignore status lines */
	toptions.c_cflag |= CREAD | CLOCAL;
	/* disable input/output flow control, disable restart chars */
	toptions.c_iflag &= ~(IXON | IXOFF | IXANY);
	/* disable canonical input, disable echo,
	disable visually erase chars,
	disable terminal-generated signals */
	toptions.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
	/* disable output processing */
	toptions.c_oflag &= ~OPOST;

	/* wait for 1 character to come in before read returns */
	/* WARNING! THIS CAUSES THE read() TO BLOCK UNTIL ALL */
	/* CHARACTERS HAVE COME IN! */
	toptions.c_cc[VMIN] = 1;
	/* no minimum time to wait before read returns */
	toptions.c_cc[VTIME] = 0;

	/* commit the options */
	tcsetattr(fd, TCSANOW, &toptions);

	/* Wait for the Arduino to reset */
	usleep(1000 * 1000);
	/* Flush anything already in the serial buffer */
	tcflush(fd, TCIFLUSH);

	msg.accelerometer_x = 11.3;
	msg.accelerometer_y = 11.3;
	msg.accelerometer_z = 11.3;
	msg.gyroscope_x = 4.5;
	msg.gyroscope_y = 5.6;
	msg.gyroscope_z = 7.1;
	// msg.imu_gyroscope= atof(gyro);
	// msg.pressure = 180;
	// msg.pressure = atof(press);
	// msg.temperature1 = 56;
	// msg.temperature2 = 56;
	// msg.temperature1 = atof(buf); // TODO: Get value from arduino
	// msg.distance = 9.0;
	// msg.distance = atof(dist);
	msg.short_dist = 12;
	// msg.long_dist = 150;

	while (stop == 0)
	{
		/* read up to 128 bytes from the fd */
		int n = read(fd, &buf, 128);
		int k = read(dl, &buf2, 128);
		usleep(500 * 1000);
		/* print how many bytes read */
		printf("%i bytes got read...\n", n);
		// printf("%i bytes got read...\n", k);
		/* print what's in the buffer */
		printf("Buffer 1 contains...\n%s\n", buf);
		printf("Buffer 2 contains...\n%s\n", buf2);
		char *token = strtok(buf, " ");
		int count = 0;
		while (token != NULL)
		{
			if (count == 0)
			{
				msg.temperature1 = atof(token);
			}
			else if (count == 1)
			{
				msg.temperature2 = atof(token);
			}
			// else if (count == 2)
			// {
			// 	// msg.accelerometer_x = atof(token);
			// }
			// else if (count == 3)
			// {
			// 	// msg.accelerometer_y = atof(token);
			// }
			// else if (count == 4)
			// {
			// 	msg.accelerometer_z = atof(token);
			// }
			// else if (count == 5)
			// {
			// 	msg.gyroscope_x = atof(token);
			// }
			// if (count == 6)
			// {
			// 	msg.gyroscope_y = atof(token);
			// }
			// if (count == 7)
			// {
			// 	msg.gyroscope_z = atof(token);
			// }
			// if (count == 8)
			// {
			// 	msg.short_dist = atof(token);
			// }
			// if (count == 9)
			// {
			// 	msg.long_dist = atof(token);
			// }
			token = strtok(NULL, " ");
			count = count + 1;
		}
		char *token2 = strtok(buf2, " ");
		int count2 = 0;
		while (token2 != NULL)
		{
			if (count2 == 0)
			{
				msg.long_dist = atof(token2);
			}
			else if (count2 == 1)
			{
				msg.pressure = atof(token2);
			}
			token2 = strtok(NULL, " ");
			count2 = count2 + 1;
		}
		// msg.temperature1 = atof(buf); // TODO: Get value from arduino
		sensor_info_t_publish(zcm, "SENSOR_INFO", &msg);
		usleep(1000000);
	}

	while (1)
	{
		sensor_info_t_publish(zcm, "SENSOR_INFO", &msg);
		usleep(1000000); /* sleep for a second */
	}

	zcm_destroy(zcm);
	return 0;
}
