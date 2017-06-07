#include <stdarg.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <sys/socket.h>
#include <resolv.h>
#include <errno.h>
#include <netdb.h>
#include <stdlib.h>
#define MAXBUF  2048
//void PANIC(char *msg);
//#define PANIC(msg)  {perror(msg); abort();}

int main(void)
{   int sockfd, bytes_read;
    struct sockaddr_in dest;
    struct hostent *myent;
    struct in_addr myen;
    char buffer[MAXBUF];
    char host[]="openapi.airkorea.or.kr";
    char url[]="http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc/getCtprvnMesureSidoLIst";
    char param[]="_returnType=json&ServiceKey=qNTKGUYOFgEj3m6dUMXBJ1ZLEPBbBX%2BQXY3d%2B77vxZgMC4RJ6TCp%2BtUw12hW%2FLgWj%2BxU10watODF73O%2Bx1essg%3D%3D&searchCondition=DAILY&pageNo=1&numOfRows=10&sidoName=%EC%9D%B8%EC%B2%9C";
    /*---Make sure we have the right number of parameters---*/
    if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0 )
        puts("Socket");
    /*---Initialize server address/port struct---*/
    bzero(&dest, sizeof(dest));
    dest.sin_family = AF_INET;
    //dest.sin_port = htons(80); /*default HTTP Server port */
	
    //if ( inet_addr(url, &dest.sin_addr.s_addr) == 0 )
    //    PANIC(url);
    myent = gethostbyname(host);
    if(myent == NULL){
	puts("error");
	exit(1);
    }
    printf("%s\n",myent->h_addr_list[0]); 	
    dest.sin_addr.s_addr=inet_addr(myent->h_addr_list[0]);
    /*---Connect to server---*/
    if ( connect(sockfd, (struct sockaddr*)&dest, sizeof(dest)) != 0 )
        puts("Connect");
    printf("OK connect"); 
    sprintf(buffer, "GET %s HTTP/1.0 \r\n\r\n", param);
    send(sockfd, buffer, strlen(buffer), 0);

    /*---While there's data, read and print it---*/
    do
    {
        bzero(buffer, sizeof(buffer));
        bytes_read = recv(sockfd, buffer, sizeof(buffer), 0);
        if ( bytes_read > 0 )
            printf("%s", buffer);
    }
    while ( bytes_read > 0 );

    /*---Clean up---*/
    close(sockfd);
    return 0;
}

