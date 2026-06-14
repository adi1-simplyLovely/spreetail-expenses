from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    expenses_paid = relationship("Expense", back_populates="payer")
    expense_splits = relationship("ExpenseSplit", back_populates="user")
    settlements_paid = relationship("Settlement", foreign_keys="[Settlement.from_user_id]", back_populates="from_user")
    settlements_received = relationship("Settlement", foreign_keys="[Settlement.to_user_id]", back_populates="to_user")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")
    settlements = relationship("Settlement", back_populates="group", cascade="all, delete-orphan")
    import_logs = relationship("ImportLog", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Group(id={self.id}, name='{self.name}')>"


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    joined_at = Column(Date, nullable=False)
    left_at = Column(Date, nullable=True) # NULL means still active

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    def __repr__(self):
        status = "Active" if not self.left_at else f"Left:{self.left_at}"
        return f"<GroupMember(group_id={self.group_id}, user_id={self.user_id}, status='{status}')>"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    description = Column(String, nullable=False)
    paid_by = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='INR')
    amount_inr = Column(Float, nullable=False)
    split_type = Column(String(20), nullable=True)
    date = Column(Date, nullable=False, index=True)
    is_settlement = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    group = relationship("Group", back_populates="expenses")
    payer = relationship("User", back_populates="expenses_paid")
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Expense(id={self.id}, desc='{self.description}', amount_inr={self.amount_inr}, date='{self.date}')>"


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount_owed = Column(Float, nullable=False)

    # Relationships
    expense = relationship("Expense", back_populates="splits")
    user = relationship("User", back_populates="expense_splits")

    def __repr__(self):
        return f"<ExpenseSplit(expense_id={self.expense_id}, user_id={self.user_id}, owed={self.amount_owed})>"


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, index=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    group = relationship("Group", back_populates="settlements")
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="settlements_paid")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="settlements_received")

    def __repr__(self):
        return f"<Settlement(from={self.from_user_id}, to={self.to_user_id}, amount={self.amount})>"


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    filename = Column(String, nullable=False)
    imported_at = Column(DateTime, default=func.now())
    total_rows = Column(Integer, nullable=True)
    imported = Column(Integer, nullable=True)
    flagged = Column(Integer, nullable=True)
    skipped = Column(Integer, nullable=True)
    report_json = Column(Text, nullable=True)

    # Relationships
    group = relationship("Group", back_populates="import_logs")

    def __repr__(self):
        return f"<ImportLog(id={self.id}, filename='{self.filename}', rows={self.total_rows})>"
