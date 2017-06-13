#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h> 

#define BUFSIZE 1024

typedef struct _weather{
	int pm10;
	int pm25;
	int	temper;	//t3h; 온도
	int	rain;	//r06; 강수량
	int	sky;
	int	rainChance;//	pop; 강수확률
	int	humid;	//reh  습도
	int	rainForm;//	pty; 강수형태 0:없음 1: 비 2: 비/눈 3: 눈
	char* time;
} Weather;

char *form[9]={"pm10","pm25","T3H","R06","SKY","POP","REH","PTY","time"};
/* 
 * error - wrapper for perror
  */
void error(char *msg) {
	perror(msg);
	exit(0);
}
char *replaceValue(char *strInput, const char *strTarget, const char *strChange);


int main(void){
	int sockfd, portno, n;
	struct sockaddr_in serveraddr;
	struct hostent *server;
	char * hostname;
	char buf[BUFSIZE];
	printf("start");

//	if(argc != 3){
//		fprint(stderr,"usage : %s <hostname> <port>\n", argv[0]);
//		exit(0);
//	}
//	hostname = argv[1];
//	portno = atoi(argv[2]);

	sockfd = socket(AF_INET,SOCK_STREAM,0);
	if(sockfd<0)
		error("Error opening socket");
	printf("whar");	
	//server = gethostbyname(hostname);
	//if(server==NULL){
	//	fprintf(stderr, "ERROR, no such host as %s\n",hostname);
	//	exit(0);
	//}
	
	printf("1");	
	bzero((char *)&serveraddr, sizeof(serveraddr));
	serveraddr.sin_family= AF_INET;
	serveraddr.sin_port = htons(56789);
	serveraddr.sin_addr.s_addr = inet_addr("127.0.0.1");


	printf("2");	
	if(connect(sockfd,(struct sockaddr*) &serveraddr, sizeof(serveraddr))<0)
		error("ERROR connecting");

	printf("Please enter msg:");
	bzero(buf,BUFSIZE);
	fgets(buf,BUFSIZE,stdin);

	n = write(sockfd,buf,strlen(buf));

	if(n<0)
		error("ERROR writinf to socket");
	
	printf("3");	
	bzero(buf,BUFSIZE);

	FILE *f;
	f=fopen("get.txt","w");
	
	n=read(sockfd, buf, BUFSIZE);
	
	if(n<0)
		error("ERROR writing to socket");
	fwrite(buf,sizeof(char),sizeof(buf),f);
	printf("echo: %s",buf);
	
	char u[]="u'";
	char up[]="'";
    
	char *result;
	result = replaceValue(buf, u,"");
	char *final;
	final = replaceValue(result,up,"");
	result =replaceValue(final,"{","");
	final = replaceValue(result,"}","");
	printf("%s",final);
	int i=0;
	char* tok[15];
	char * ptr=strtok(final,",");
	while(ptr != NULL){
		tok[i]=ptr;
		i++;
		ptr = strtok(NULL,",");
	}
	
	Weather weatherData;
	int j = i;
	int k;
	for(i=0;i<j;i++){
		//printf("%s\n",tok[i]);
		char *tmp,*tmp2;
		tmp = strtok(tok[i],":");
		tmp=replaceValue(tmp," ","");
		tmp2 = strtok(NULL,":");
		tmp2=replaceValue(tmp2," ","");
		//printf("%s-->",tmp);
		//printf("%s\n",tmp2);

		for(k=0;k<9;k++){
			if(strcmp(form[k], tmp)==0){
				switch(k){	
				case 0:
					weatherData.pm10 = atoi(tmp2);
					break;
				case 1:
					weatherData.pm25 = atoi(tmp2);
					break;
				case 2:
					weatherData.temper = atoi(tmp2);
					break;
				case 3:
					weatherData.rain = atoi(tmp2);
					break;
				case 4:
					weatherData.sky = atoi(tmp2);
					break;
				case 5: 
					weatherData.rainChance = atoi(tmp2);
					break;
				case 6:
					weatherData.humid = atoi(tmp2);
					break;
				case 7:
					weatherData.rainForm = atoi(tmp2);
					break;
				case 8:
					weatherData.time = tmp2;
					break;
				}
				break;
			}
				
		}

	}
	//printf("%d ! %d  !  %d !  %d !  %d  !  %d ! %d !  %d  ! %s", weatherData.pm10,weatherData.pm25,weatherData.temper,weatherData.rain,weatherData.sky,weatherData.rainChance,weatherData.humid,weatherData.rainForm,weatherData.time);

	return 0;
}
char *replaceValue(char *strInput, const char *strTarget, const char *strChange)
{
    char* strResult;
	char* strTemp;
	int i = 0;
	int nCount = 0;
	int nTargetLength = strlen(strTarget);
				 
	if (nTargetLength < 1)
		return strInput;
								  
	int nChangeLength = strlen(strChange);
									   
	if (nChangeLength != nTargetLength)
	{
		for (i = 0; strInput[i] != '\0';)
		{
			if (memcmp(&strInput[i], strTarget, nTargetLength) == 0)
			{
				nCount++;
				i += nTargetLength;
			}
			else i++;
		}
	}
	else
	{
	   i = strlen(strInput);
	}
	strResult = (char *) malloc(i + 1 + nCount * (nChangeLength - nTargetLength));
	if (strResult == NULL) return NULL;
		strTemp = strResult;
	while (*strInput)
	{
		if (memcmp(strInput, strTarget, nTargetLength) == 0)
		{
			memcpy(strTemp, strChange, nChangeLength);
			strTemp += nChangeLength;
			strInput  += nTargetLength;
		}else{
			*strTemp++ = *strInput++;
		}
	}
	*strTemp = '\0';
	
	return strResult;
}
