#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <curl/curl.h>

static size_t write_data(void *ptr, size_t size, size_t nmemb, void *stream){
    size_t written = fwrite(ptr,size,nmemb,(FILE *)stream);

    return written;
}

int main(void)
{
      CURL *curl;
      static const char* pagefilename="mise.json";
      FILE *pagefile;
      CURLcode res;

      curl = curl_easy_init();
      char* url = "http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc/getCtprvnMesureSidoLIst?sidoName=%EC%9D%B8%EC%B2%9C&searchCondition=DAILY&pageNo=1&numOfRows=10&ServiceKey=qNTKGUYOFgEj3m6dUMXBJ1ZLEPBbBX%2BQXY3d%2B77vxZgMC4RJ6TCp%2BtUw12hW%2FLgWj%2BxU10watODF73O%2Bx1essg%3D%3D&_returnType=json&ver=1.3";
      if(curl) {
	  curl_easy_setopt(curl, CURLOPT_URL, url);
	/* example.com is redirected, so we tell libcurl to follow redirection */ 
	  curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
	  curl_easy_setopt(curl, CURLOPT_NOPROGRESS,1L);
	  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);

	  pagefile = fopen(pagefilename,"wb");
	  if(pagefile){
	  	curl_easy_setopt(curl,CURLOPT_WRITEDATA,pagefile);

		curl_easy_perform(curl);

		fclose(pagefile);
	  
	  }
			 
	  /* Perform the request, res will get the return code */ 
	 // res = curl_easy_perform(curl);
	 /* Check for errors */ 
	  curl_easy_cleanup(curl);
      }
      return 0;
}
