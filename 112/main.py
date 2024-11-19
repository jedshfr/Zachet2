from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QWidget, QLabel, QInputDialog, QListWidgetItem
)
from PySide6.QtGui import QIcon
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
# Создаем базу данных
Base = declarative_base()

# Таблица связи "многие-ко-многим"
class NoteTag(Base):
    __tablename__ = 'note_tags'
    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey('notes.id_notes'))
    tag_id = Column(Integer, ForeignKey('tags.id_tags'))

    # Связь с таблицами Note и Tag
    note = relationship("Note", back_populates="note_tags")
    tag = relationship("Tag", back_populates="note_tags")

# Модель заметок
class Note(Base):
    __tablename__ = 'notes'
    id_notes = Column(Integer, primary_key=True)
    texts = Column(String)

    # Связь с таблицей NoteTag
    note_tags = relationship("NoteTag", back_populates="note")
    # Связь с тегами через таблицу NoteTag
    tags = relationship(
        "Tag",
        secondary="note_tags",
        primaryjoin="Note.id_notes==NoteTag.note_id",
        secondaryjoin="Tag.id_tags==NoteTag.tag_id",
        viewonly=False
    )

# Модель тегов
class Tag(Base):
    __tablename__ = 'tags'
    id_tags = Column(Integer, primary_key=True)
    names = Column(String(50))

    # Связь с таблицей NoteTag
    note_tags = relationship("NoteTag", back_populates="tag")
    # Связь с заметками через таблицу NoteTag
    notes = relationship(
        "Note",
        secondary="note_tags",
        primaryjoin="Tag.id_tags==NoteTag.tag_id",
        secondaryjoin="Note.id_notes==NoteTag.note_id",
        viewonly=False
    )

# Настройка базы данных
engine = create_engine('postgresql://postgres@localhost:5432/za')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Функции для работы с заметками
def add_note(text, tag_names):
    tags = []
    for tag_name in tag_names:
        tag = session.query(Tag).filter_by(names=tag_name).first()
        if not tag:
            tag = Tag(names=tag_name)
        tags.append(tag)
    note = Note(texts=text, tags=tags)
    session.add(note)
    session.commit()

def delete_note(note_id):
    note = session.query(Note).get(note_id)
    if note:
        # Удалить связанные записи в NoteTag
        session.query(NoteTag).filter_by(note_id=note_id).delete()
        # Удалить заметку
        session.delete(note)
        session.commit()

def edit_note(note_id, new_text):
    note = session.query(Note).get(note_id)
    if note:
        note.texts = new_text
        session.commit()

def search_notes_by_tag(tag_name):
    tag = session.query(Tag).filter_by(names=tag_name).first()
    return tag.notes if tag else []

# Графический интерфейс
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Заметки с тегами")
        self.setWindowIcon(QIcon("1.png"))  # Установите путь к иконке
       
        self.layout = QVBoxLayout()
       
        # Поле для ввода текста заметки
        self.note_input = QTextEdit()
        self.layout.addWidget(QLabel("Введите текст заметки:"))
        self.layout.addWidget(self.note_input)
       
        # Поле для ввода тегов
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Введите теги через запятую")
        self.layout.addWidget(self.tag_input)
       
        # Кнопка добавления заметки
        self.add_button = QPushButton("Добавить заметку")
        self.add_button.clicked.connect(self.add_note)
        self.layout.addWidget(self.add_button)
       
        # Список заметок
        self.notes_list = QListWidget()
        self.layout.addWidget(QLabel("Заметки:"))
        self.layout.addWidget(self.notes_list)
       
        # Кнопки для удаления и редактирования
        self.delete_button = QPushButton("Удалить заметку")
        self.delete_button.clicked.connect(self.delete_note)
        self.layout.addWidget(self.delete_button)
       
        self.edit_button = QPushButton("Редактировать заметку")
        self.edit_button.clicked.connect(self.edit_note)
        self.layout.addWidget(self.edit_button)
       
        # Поле для поиска заметок по тегам
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите тег для поиска")
        self.layout.addWidget(QLabel("Поиск заметок по тегу:"))
        self.layout.addWidget(self.search_input)
       
        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.search_notes)
        self.layout.addWidget(self.search_button)
       
        # Установка центрального виджета
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        self.update_notes_list()

    def add_note(self):
        text = self.note_input.toPlainText().strip()
        tags = self.tag_input.text().strip().split(',')
        if text:
            add_note(text, [tag.strip() for tag in tags])
            self.note_input.clear()
            self.tag_input.clear()
            self.update_notes_list()

    def delete_note(self):
        selected_items = self.notes_list.selectedItems()
        if selected_items:
            note_id = int(selected_items[0].data(256))  # Получение ID заметки
            delete_note(note_id)
            self.update_notes_list()

    def edit_note(self):
        selected_items = self.notes_list.selectedItems()
        if selected_items:
            note_id = int(selected_items[0].data(256))
            new_text, ok = QInputDialog.getText(self, "Редактирование заметки", "Введите новый текст:")
            if ok and new_text:
                edit_note(note_id, new_text)
                self.update_notes_list()

    def search_notes(self):
        tag_name = self.search_input.text().strip()
        if tag_name:
            notes = search_notes_by_tag(tag_name)
            self.notes_list.clear()
            for note in notes:
                item = QListWidgetItem(f"ID {note.id_notes}: {note.texts}")
                item.setData(256, note.id_notes)
                self.notes_list.addItem(item)
    def update_notes_list(self):
        self.notes_list.clear()
        notes = session.query(Note).all()
        for note in notes:
            item = QListWidgetItem(f"ID {note.id_notes}: {note.texts}")
            item.setData(256, note.id_notes)
            self.notes_list.addItem(item)

app = QApplication([])
window = MainApp()
window.show()
app.exec()