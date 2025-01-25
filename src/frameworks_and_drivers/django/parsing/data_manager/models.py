from django.db import models


class GenericModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(GenericModel):
    username = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.username}"


class MacroCategory(models.Model):
    name = models.CharField(max_length=250, db_index=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="images_macrocategory", max_length=300, blank=True, null=True)

    def __str__(self):
        return self.name


class Tags(GenericModel):
    name = models.CharField(max_length=250, db_index=True)
    description = models.TextField()
    image = models.ImageField(upload_to="images_tag", max_length=300)
    macro_category = models.ForeignKey(MacroCategory, on_delete=models.SET_NULL, related_name="tags", null=True,
                                       blank=True)

    def __str__(self):
        return f"{self.name}"


class Content(GenericModel):
    name = models.CharField(max_length=250)
    description = models.TextField()
    tags = models.ManyToManyField(Tags, related_name='contents')
    image = models.ImageField(upload_to="images", max_length=300)
    contact = models.JSONField(default={}, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.CharField(max_length=250, null=True, blank=True, default=None)
    location = models.CharField(max_length=250, null=True, blank=True, default=None)
    cost = models.IntegerField(null=True, blank=True, default=None)

    def get_tags(self):
        return "\n".join([t.name for t in self.tags.all()])

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ["date"]


class Like(GenericModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='likes')
    value = models.BooleanField()

    class Meta:
        unique_together = (
            "user",
            "content",
        )

    def __str__(self):
        return f"{self.user.username} - {self.content.name} - {self.value} - {self.created}"


class Feedback(GenericModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    message = models.TextField()


class RemovedFavorite(models.Model):
    """Эта таблица будет фиксировать, что пользователь исключил конкретный контент из избранного."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    removed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content')


class UserCategoryPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category_preferences")
    tag = models.ForeignKey(Tags, on_delete=models.CASCADE, related_name="user_preferences")

    class Meta:
        unique_together = ('user', 'tag')

    def __str__(self):
        return f"{self.user.username} - {self.tag.name}"
