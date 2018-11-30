#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>

const int N_qsort = 10000;
const int N_int   = 10000;
const int N_float = 20000;
const int N_pi    = 50000000;

int thread_count = 0;
void int_comp(void);
void float_comp(void);
void pi_comp(void);
void to_qsort(int arr[],int low,int high);
void qsort_comp(void);
void thread(void);
void thread_int(void);
void thread_float(void);
void thread_pi(void);
void thread_qsort(void);

int main(int argc,char** argv){
	int count,i,result,type;
	count = atoi(argv[1]);
	type =  atoi(argv[2]);
	if(argc < 3){
		printf("ERROR: Parameter error[%d]",argc);
	}
	pthread_t tid;
	for(i=0;i<count;i++){
		switch(type){
			case 1:
				pthread_create(&tid,NULL,(void *) thread_int,NULL);
				break;
			case 2:
				pthread_create(&tid,NULL,(void *) thread_float,NULL);
				break;
			case 3:
				pthread_create(&tid,NULL,(void *) thread_pi,NULL);
				break;
			case 4:
				pthread_create(&tid,NULL,(void *) thread_qsort,NULL);
				break;
			default:
				pthread_create(&tid,NULL,(void *) thread,NULL);
				break;
		}
		
	}
	
	while(thread_count != count){
		sleep(0.1);
	}
	return 0;
}

void thread(void){
	int_comp();
	float_comp();
	pi_comp();
	qsort_comp();
	thread_count++;
}

void thread_int(void){
	int_comp();
	thread_count++;
}

void thread_float(void){
	float_comp();
	thread_count++;
}

void thread_pi(void){
	pi_comp();
	thread_count++;
}

void thread_qsort(void){
	qsort_comp();
	thread_count++;
}

void int_comp(void){
     int i,j;
     for(i=0;i<N_int;i++)
         for(j=0;j<N_float;j++);
}

void float_comp(void){
     float i,j;
     for(i=0;i<N_int;i++)
     	for(j=0;j<N_float;j++);
}

void pi_comp(void){
     int m,i=1;
     double s=0;
     for(m=1;m<N_pi;m+=2){
        s+=i*(1.0/m);
        i=-i;
     }
}

void to_qsort(int arr[],int low,int high){
     if(low>=high) return;
     int first=low;
     int last=high;
     int key=arr[first];
     while(first<last){
         while(first<last&&arr[last]>=key) --last;
         arr[first]=arr[last];
         while(first<last&&arr[first]<=key) ++first;
         arr[last]=arr[first];
     }
     arr[first]=key;
     to_qsort(arr,low,first-1);
     to_qsort(arr,first+1,high);
}

void qsort_comp(void){
     int arr[N_qsort],i;
     for(i=N_qsort;i>0;i--) arr[N_qsort-1]=i;
     to_qsort(arr,0,N_qsort-1);
}