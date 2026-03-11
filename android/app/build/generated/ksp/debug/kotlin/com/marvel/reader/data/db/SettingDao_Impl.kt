package com.marvel.reader.`data`.db

import androidx.room.EntityDeleteOrUpdateAdapter
import androidx.room.EntityInsertAdapter
import androidx.room.EntityUpsertAdapter
import androidx.room.RoomDatabase
import androidx.room.util.getColumnIndexOrThrow
import androidx.room.util.performSuspending
import androidx.sqlite.SQLiteStatement
import javax.`annotation`.processing.Generated
import kotlin.Int
import kotlin.String
import kotlin.Suppress
import kotlin.Unit
import kotlin.collections.List
import kotlin.collections.MutableList
import kotlin.collections.mutableListOf
import kotlin.reflect.KClass

@Generated(value = ["androidx.room.RoomProcessor"])
@Suppress(names = ["UNCHECKED_CAST", "DEPRECATION", "REDUNDANT_PROJECTION", "REMOVAL"])
public class SettingDao_Impl(
  __db: RoomDatabase,
) : SettingDao {
  private val __db: RoomDatabase

  private val __upsertAdapterOfSettingEntity: EntityUpsertAdapter<SettingEntity>
  init {
    this.__db = __db
    this.__upsertAdapterOfSettingEntity = EntityUpsertAdapter<SettingEntity>(object :
        EntityInsertAdapter<SettingEntity>() {
      protected override fun createQuery(): String =
          "INSERT INTO `settings` (`key`,`value`) VALUES (?,?)"

      protected override fun bind(statement: SQLiteStatement, entity: SettingEntity) {
        statement.bindText(1, entity.key)
        statement.bindText(2, entity.value)
      }
    }, object : EntityDeleteOrUpdateAdapter<SettingEntity>() {
      protected override fun createQuery(): String =
          "UPDATE `settings` SET `key` = ?,`value` = ? WHERE `key` = ?"

      protected override fun bind(statement: SQLiteStatement, entity: SettingEntity) {
        statement.bindText(1, entity.key)
        statement.bindText(2, entity.value)
        statement.bindText(3, entity.key)
      }
    })
  }

  public override suspend fun upsert(setting: SettingEntity): Unit = performSuspending(__db, false,
      true) { _connection ->
    __upsertAdapterOfSettingEntity.upsert(_connection, setting)
  }

  public override suspend fun `get`(key: String): SettingEntity? {
    val _sql: String = "SELECT * FROM settings WHERE `key` = ?"
    return performSuspending(__db, true, false) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        var _argIndex: Int = 1
        _stmt.bindText(_argIndex, key)
        val _cursorIndexOfKey: Int = getColumnIndexOrThrow(_stmt, "key")
        val _cursorIndexOfValue: Int = getColumnIndexOrThrow(_stmt, "value")
        val _result: SettingEntity?
        if (_stmt.step()) {
          val _tmpKey: String
          _tmpKey = _stmt.getText(_cursorIndexOfKey)
          val _tmpValue: String
          _tmpValue = _stmt.getText(_cursorIndexOfValue)
          _result = SettingEntity(_tmpKey,_tmpValue)
        } else {
          _result = null
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public override suspend fun getAll(): List<SettingEntity> {
    val _sql: String = "SELECT * FROM settings"
    return performSuspending(__db, true, false) { _connection ->
      val _stmt: SQLiteStatement = _connection.prepare(_sql)
      try {
        val _cursorIndexOfKey: Int = getColumnIndexOrThrow(_stmt, "key")
        val _cursorIndexOfValue: Int = getColumnIndexOrThrow(_stmt, "value")
        val _result: MutableList<SettingEntity> = mutableListOf()
        while (_stmt.step()) {
          val _item: SettingEntity
          val _tmpKey: String
          _tmpKey = _stmt.getText(_cursorIndexOfKey)
          val _tmpValue: String
          _tmpValue = _stmt.getText(_cursorIndexOfValue)
          _item = SettingEntity(_tmpKey,_tmpValue)
          _result.add(_item)
        }
        _result
      } finally {
        _stmt.close()
      }
    }
  }

  public companion object {
    public fun getRequiredConverters(): List<KClass<*>> = emptyList()
  }
}
