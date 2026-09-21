import os


def remove_lock_files(user_id, base_dirs, system_log):
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.endswith('.lock'):
                        file_path = os.path.join(root, file)
                        try:
                            os.unlink(file_path)
                        except BaseException:
                            system_log.error(user_id, file_path)
