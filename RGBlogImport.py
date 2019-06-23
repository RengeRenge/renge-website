from flask import json

from DAO import rg_dao as dao
from Model import article


def do_import(filename, user_id):
    with open('../%s' % filename, 'r') as f:
        blog_json = json.loads(f.read())
        do_parse_json(blog_json['root']['blog'], user_id)
        f.close()


def do_parse_json(blogs, user_id):
    conn = None
    try:
        conn = dao.get()

        class_id_map = {}

        for blog in blogs:
            title = blog['title']
            publish_time = int(blog['publishTime'])
            class_id = blog['classId']
            class_name = blog['className']
            content = blog['content']
            content = change_img_path(content)

            if class_id not in class_id_map:
                new_group_sql = article.new_group_sql()
                args = {
                    'name': class_name,
                    'user_id': user_id,
                    'order': 0,
                    'level': 2
                }
                res, count, new_id, err = dao.do_execute_sql_with_connect(
                    sql=new_group_sql,
                    neednewid=True,
                    args=args,
                    conn=conn,
                    commit=False
                )

                if err or count is 0:
                    raise Exception('new group failed')
                else:
                    class_id_map[class_id] = new_id

            group_id = class_id_map[class_id]
            article.add_or_update_art(
                user_id=user_id,
                title=title,
                content=content,
                cate=0,
                group_id=group_id,
                conn=conn,
                commit=False,
                timestamp=publish_time)
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
    finally:
        if conn:
            conn.close()


def change_img_path(content):
    new_content = content
    with open('../imageKeys.txt', 'r') as keys:
        with open('../imageValues.txt', 'r') as values:
            while True:
                key = keys.readline().rstrip('\n')
                value = values.readline().rstrip('\n')
                if len(key) is 0 or len(value) is 0:
                    break
                else:
                    value = '/file/import/' + value
                    new_content = new_content.replace(key, value)
            values.close()
            keys.close()
            return new_content


if __name__ == '__main__':
    do_import('blog.json', 4)
