class GitSkill:
    def run(self, task, tools):
        branch = tools['create_branch'].run({"branch_name": f"task-{task.id}-dev"})
        diff = tools['diff'].run({"id": task.id})
        tools["commit"].run(diff)
        pass