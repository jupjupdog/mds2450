#include <stdio.h>
#include <jansson.h>

void insert_filename(json_t* pjson,char* filename){
    json_t* data;
    data = json_string(filename);
    json_array_append(pjson,data);
}

int main(int argc, char** argv){
    json_t* pjson;
    json_t* data;
    int i;
    char* result;

    pjson=json_array();

    for(i=1; i<= argc; i++)
	insert_filename(pjson, argv[i]);

    printf("size : %d\n", json_array_size(pjson));
    result = json_dumps(pjson, JSON_ENCODE_ANY);
    json_dump_file(pjson, "./data.json",JSON_ENCODE_ANY);
    printf("%s\n",result);

    json_decref(pjson);

    return 0;

}
