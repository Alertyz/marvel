package com.marvel.reader.`data`.db

import androidx.room.EntityDeleteOrUpdateAdapter
import androidx.room.EntityInsertAdapter
import androidx.room.EntityUpsertAdapter
import androidx.room.RoomDatabase
import androidx.room.coroutines.createFlow
import androidx.room.util.getColumnIndexOrThrow
import androidx.room.util.performSuspending
import androidx.sqlite.SQLiteStatement
import javax.`annotation`.processing.Generated
import kotlin.Boolean
import kotlin.Int
import kotlin.String
import kotlin.Suppress
import kotlin.Unit
import kotlin.collections.List
import kotlin.collections.MutableList
import kotlin.collections.mutableListOf
import kotlin.reflect.KClass
import kotlinx.coroutines.flow.Flow

@Generated(value = ["androidx.room.RoomProcessor"])
@Suppress(names = ["UNCHECKED_CAST", "DEPRECATION", "REDUNDANT_PROJECTION", "REMOVAL"])
public class ProgressDao_Impl(
  __db: RoomDatabase,
) : ProgressDao {
  private val __db: RoomDatabase

  private val __upsertAdapterOfProgressEntity: EntityUpsertAdapter<ProgressEntity>
  init {
    this.__db = __db
    this.__upsertAdapterOfProgressEntity = EntityUpsertAdapter<ProgressEntity>(object :
        EntityInsertAdapter<ProgressEntity>() {
      protected override fun createQuery(): String =
          "INSERT INTO `reading_progress` (`orderNum`,`currentPage`,`isRead`,`updatedAt`) VALUES (?,?,?,?)"

      protected override fun bind(statement: SQLiteStatement, entity: ProgressEntity) {
        statement.bindLong(1, entity.orderNum.toLong())
        statement.bindLong(2, entity.currentPage.toLong())
        val _tmp: Int = if (entity.isRead) 1 else 0
        statement.bindLong(3, _tmp.toLong())
        statement.bindText(4, entity.updatedAt)
      }
    }, object : EntityDeleteOrUpdateAdapter<ProgressEntity>() {
      protected override fun createQuery(): String =
          "UPDATE `reading_progress` SET `orderNum` = ?,`currentPage` = ?,`isRead` = ?,`updatedAt` = ? WHERE `orderNum` = ?"

      protected override fun bind(statement: SQLiteStatement, entity: ProgressEntity) {
        statement.bindLong(1, entity.orderNum.toLong())
        statement.bindLong(2, entity.currentPage.toLong())
        val _tmp: Int = if (entity.isRead) 1 else 0
        statement.bindLong(3, _tmp.toLong())
        statement.bindText(4, entity.updatedAt)
        statement.bindLong(5, entity.orderNum.toLong())
      }
    })
  }

  public override suspend fun upsert(progress: ProgressEntity): Unit = performSuspending(__db,
      false, true) { _connection ->
    __upsertAdapterOfProgressEntity.upsert(_connection, progress)
  }

  public override suspend fun upsertAll(list: List<ProgressEntity>): Unit = performSuspending(__db,
      false, true) { _connection ->
    __upsertAdapterOfProgressEntity.upsert(_connection, list)
  }

  public override suspend fun `get`(orderNum: Int): ProgressEntity? {
    val _sql: String = "SELECT * FROM reading_progress WHERE orderNum = ?"
    return performSuspending(__db, true, false) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        var _argIndex: Int = 1
        _stmt.bindLong(_argIndex, orderNum.toLong())
        val _cursorIndexOfOrderNum: Int = getColumnIndexOrThrow(_stmt, "orderNum")
        val _cursorIndexOfCurrentPage: Int = getColumnIndexOrThrow(_stmt, "currentPage")
        val _cursorIndexOfIsRead: Int = getColumnIndexOrThrow(_stmt, "isRead")
        val _cursorIndexOfUpdatedAt: Int = getColumnIndexOrThrow(_stmt, "updatedAt")
        val _result: ProgressEntity?
        if (_stmt.step()) {
          val _tmpOrderNum: Int
          _tmpOrderNum = _stmt.getLong(_cursorIndexOfOrderNum).toInt()
          val _tmpCurrentPage: Int
          _tmpCurrentPage = _stmt.getLong(_cursorIndexOfCurrentPage).toInt()
          val _tmpIsRead: Boolean
          val _tmp: Int
          _tmp = _stmt.getLong(_cursorIndexOfIsRead).toInt()
          _tmpIsRead = _tmp != 0
          val _tmpUpdatedAt: String
          _tmpUpdatedAt = _stmt.getText(_cursorIndexOfUpdatedAt)
          _result = ProgressEntity(_tmpOrderNum,_tmpCurrentPage,_tmpIsRead,_tmpUpdatedAt)
        } else {
          _result = null
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override suspend fun getAll(): List<ProgressEntity> {
    val _sql: String = "SELECT * FROM reading_progress"
    return performSuspending(__db, true, false) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        val _cursorIndexOfOrderNum: Int = getColumnIndexOrThrow(_stmt, "orderNum")
        val _cursorIndexOfCurrentPage: Int = getColumnIndexOrThrow(_stmt, "currentPage")
        val _cursorIndexOfIsRead: Int = getColumnIndexOrThrow(_stmt, "isRead")
        val _cursorIndexOfUpdatedAt: Int = getColumnIndexOrThrow(_stmt, "updatedAt")
        val _result: MutableList<ProgressEntity> = mutableListOf()
        while (_stmt.step()) {
          val _item: ProgressEntity
          val _tmpOrderNum: Int
          _tmpOrderNum = _stmt.getLong(_cursorIndexOfOrderNum).toInt()
          val _tmpCurrentPage: Int
          _tmpCurrentPage = _stmt.getLong(_cursorIndexOfCurrentPage).toInt()
          val _tmpIsRead: Boolean
          val _tmp: Int
          _tmp = _stmt.getLong(_cursorIndexOfIsRead).toInt()
          _tmpIsRead = _tmp != 0
          val _tmpUpdatedAt: String
          _tmpUpdatedAt = _stmt.getText(_cursorIndexOfUpdatedAt)
          _item = ProgressEntity(_tmpOrderNum,_tmpCurrentPage,_tmpIsRead,_tmpUpdatedAt)
          _result.add(_item)
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override fun allFlow(): Flow<List<ProgressEntity>> {
    val _sql: String = "SELECT * FROM reading_progress"
    return createFlow(__db, false, arrayOf("reading_progress")) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        val _cursorIndexOfOrderNum: Int = getColumnIndexOrThrow(_stmt, "orderNum")
        val _cursorIndexOfCurrentPage: Int = getColumnIndexOrThrow(_stmt, "currentPage")
        val _cursorIndexOfIsRead: Int = getColumnIndexOrThrow(_stmt, "isRead")
        val _cursorIndexOfUpdatedAt: Int = getColumnIndexOrThrow(_stmt, "updatedAt")
        val _result: MutableList<ProgressEntity> = mutableListOf()
        while (_stmt.step()) {
          val _item: ProgressEntity
          val _tmpOrderNum: Int
          _tmpOrderNum = _stmt.getLong(_cursorIndexOfOrderNum).toInt()
          val _tmpCurrentPage: Int
          _tmpCurrentPage = _stmt.getLong(_cursorIndexOfCurrentPage).toInt()
          val _tmpIsRead: Boolean
          val _tmp: Int
          _tmp = _stmt.getLong(_cursorIndexOfIsRead).toInt()
          _tmpIsRead = _tmp != 0
          val _tmpUpdatedAt: String
          _tmpUpdatedAt = _stmt.getText(_cursorIndexOfUpdatedAt)
          _item = ProgressEntity(_tmpOrderNum,_tmpCurrentPage,_tmpIsRead,_tmpUpdatedAt)
          _result.add(_item)
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override suspend fun markAllBeforeAsRead(orderNum: Int, timestamp: String) {
    val _sql: String = "UPDATE reading_progress SET isRead = 1, updatedAt = ? WHERE orderNum <= ?"
    return performSuspending(__db, false, true) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        var _argIndex: Int = 1
        _stmt.bindText(_argIndex, timestamp)
        _argIndex = 2
        _stmt.bindLong(_argIndex, orderNum.toLong())
        _stmt.step()
      } finally {
        _stmt.close()
      }
    }
  }

  public companion object {
    public fun getRequiredConverters(): List<KClass<*>> = emptyList()
  }
}
