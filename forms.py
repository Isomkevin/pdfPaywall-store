from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from replit import db
from wtforms import FloatField, StringField, SubmitField, TextAreaField, ValidationError
from wtforms.validators import InputRequired, Length, NumberRange


def name_to_id(name):
  return name.lower().replace(" ", "-")


class ContentCreateForm(FlaskForm):
  name = StringField("Title", validators=[InputRequired(), Length(3)])

  description = TextAreaField("Description", validators=[InputRequired()])

  file = FileField(
      "PDF file",
      validators=[FileRequired(),
                  FileAllowed(['pdf'], "PDFS only")])

  image = FileField("Preview image",
                    validators=[
                        FileRequired(),
                        FileAllowed(['jpg', 'jpeg', 'png', 'svg'],
                                    "Images only.")
                    ])

  price = FloatField("Price in USD (0 = free)",
                     validators=[InputRequired(),
                                 NumberRange(0)])

  submit = SubmitField("Create content")

  def validate_name(form, field):
    if name_to_id(field) in db["content"]:
      raise ValidationError("Content name already taken")
