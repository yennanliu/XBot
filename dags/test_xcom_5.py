from airflow import DAG
from airflow.operators.python_operator       import PythonOperator
from airflow.operators.dummy_operator        import DummyOperator
from airflow.operators.bash_operator       import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import os

value_1 = [1, 2, 3]
value_2 = {'a': 'b'}


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2021, 3, 1, 0, 0),
    'retries': 5,
    'retry_delay': timedelta(minutes=1),
    'provide_context' : True # https://stackoverflow.com/questions/52541911/keyerror-ti-in-apache-airflow-xcom
}

dag = DAG('test_xcom_5',
    default_args = default_args)

def push1(**kwargs):
    print ("*"*30)
    print (os.getcwd())
    print ("*"*30)
    result = []
    with open("/Users/yennan.liu/airflow/data/company.txt") as f:
        data = f.readlines()
        result.append(data)
    kwargs['ti'].xcom_push(key='value from pusher 1', value=str(result))

def push2(**kwargs):
    """Pushes an XCom without a specific target, just by returning it"""
    return value_2

def pull1(**kwargs):
    ti = kwargs['ti']
    pulled_value_1 = ti.xcom_pull(key=None, task_ids='push1')
    print ("*** pulled_value_1 = " + str(pulled_value_1))


def pull2(**kwargs):
    ti = kwargs['ti']
    pulled_value_2 = ti.xcom_pull(task_ids='push2')
    print ("*** pulled_value_2 = " + str(pulled_value_2))


push1 = PythonOperator(
    task_id='push1',
    python_callable=push1,
    dag = dag
)

push2 = PythonOperator(
    task_id='push2',
    python_callable=push2,
    dag = dag
)


bash_cmd="""data="`cat /Users/yennan.liu/airflow/data/company.txt`" && echo $data"""

push3 = BashOperator(
    task_id='push3',
    bash_command=bash_cmd,
    xcom_push=True,
    dag=dag)

pull1 = PythonOperator(
    task_id='pull1',
    python_callable=pull1,
    dag = dag
)

pull2 = PythonOperator(
    task_id='pull2',
    python_callable=pull2,
    dag = dag
)

pull3 = BashOperator(
    task_id='pull3',
    bash_command="echo {{ ti.xcom_pull(task_ids='push3') }}",
    xcom_push=True,
    dag=dag)

end = DummyOperator(task_id = 'end', retries = 0, dag=dag)


push1 >> pull1 >> end
push2 >> pull2 >> end
push3 >> pull3 >> end
