package com.marvel.reader.data.db;

import android.database.Cursor;
import android.os.CancellationSignal;
import androidx.annotation.NonNull;
import androidx.room.CoroutinesRoom;
import androidx.room.EntityDeletionOrUpdateAdapter;
import androidx.room.EntityInsertionAdapter;
import androidx.room.EntityUpsertionAdapter;
import androidx.room.RoomDatabase;
import androidx.room.RoomSQLiteQuery;
import androidx.room.util.CursorUtil;
import androidx.room.util.DBUtil;
import androidx.sqlite.db.SupportSQLiteStatement;
import java.lang.Class;
import java.lang.Exception;
import java.lang.Integer;
import java.lang.Long;
import java.lang.Object;
import java.lang.Override;
import java.lang.String;
import java.lang.SuppressWarnings;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Callable;
import javax.annotation.processing.Generated;
import kotlin.Unit;
import kotlin.coroutines.Continuation;
import kotlinx.coroutines.flow.Flow;

@Generated("androidx.room.RoomProcessor")
@SuppressWarnings({"unchecked", "deprecation"})
public final class ReportDao_Impl implements ReportDao {
  private final RoomDatabase __db;

  private final EntityInsertionAdapter<ReportEntity> __insertionAdapterOfReportEntity;

  private final EntityUpsertionAdapter<ReportEntity> __upsertionAdapterOfReportEntity;

  public ReportDao_Impl(@NonNull final RoomDatabase __db) {
    this.__db = __db;
    this.__insertionAdapterOfReportEntity = new EntityInsertionAdapter<ReportEntity>(__db) {
      @Override
      @NonNull
      protected String createQuery() {
        return "INSERT OR ABORT INTO `reports` (`id`,`issueOrder`,`pageNum`,`reportType`,`description`,`resolved`,`createdAt`) VALUES (nullif(?, 0),?,?,?,?,?,?)";
      }

      @Override
      protected void bind(@NonNull final SupportSQLiteStatement statement,
          @NonNull final ReportEntity entity) {
        statement.bindLong(1, entity.getId());
        statement.bindLong(2, entity.getIssueOrder());
        if (entity.getPageNum() == null) {
          statement.bindNull(3);
        } else {
          statement.bindLong(3, entity.getPageNum());
        }
        statement.bindString(4, entity.getReportType());
        statement.bindString(5, entity.getDescription());
        final int _tmp = entity.getResolved() ? 1 : 0;
        statement.bindLong(6, _tmp);
        statement.bindString(7, entity.getCreatedAt());
      }
    };
    this.__upsertionAdapterOfReportEntity = new EntityUpsertionAdapter<ReportEntity>(new EntityInsertionAdapter<ReportEntity>(__db) {
      @Override
      @NonNull
      protected String createQuery() {
        return "INSERT INTO `reports` (`id`,`issueOrder`,`pageNum`,`reportType`,`description`,`resolved`,`createdAt`) VALUES (nullif(?, 0),?,?,?,?,?,?)";
      }

      @Override
      protected void bind(@NonNull final SupportSQLiteStatement statement,
          @NonNull final ReportEntity entity) {
        statement.bindLong(1, entity.getId());
        statement.bindLong(2, entity.getIssueOrder());
        if (entity.getPageNum() == null) {
          statement.bindNull(3);
        } else {
          statement.bindLong(3, entity.getPageNum());
        }
        statement.bindString(4, entity.getReportType());
        statement.bindString(5, entity.getDescription());
        final int _tmp = entity.getResolved() ? 1 : 0;
        statement.bindLong(6, _tmp);
        statement.bindString(7, entity.getCreatedAt());
      }
    }, new EntityDeletionOrUpdateAdapter<ReportEntity>(__db) {
      @Override
      @NonNull
      protected String createQuery() {
        return "UPDATE `reports` SET `id` = ?,`issueOrder` = ?,`pageNum` = ?,`reportType` = ?,`description` = ?,`resolved` = ?,`createdAt` = ? WHERE `id` = ?";
      }

      @Override
      protected void bind(@NonNull final SupportSQLiteStatement statement,
          @NonNull final ReportEntity entity) {
        statement.bindLong(1, entity.getId());
        statement.bindLong(2, entity.getIssueOrder());
        if (entity.getPageNum() == null) {
          statement.bindNull(3);
        } else {
          statement.bindLong(3, entity.getPageNum());
        }
        statement.bindString(4, entity.getReportType());
        statement.bindString(5, entity.getDescription());
        final int _tmp = entity.getResolved() ? 1 : 0;
        statement.bindLong(6, _tmp);
        statement.bindString(7, entity.getCreatedAt());
        statement.bindLong(8, entity.getId());
      }
    });
  }

  @Override
  public Object insert(final ReportEntity report, final Continuation<? super Long> $completion) {
    return CoroutinesRoom.execute(__db, true, new Callable<Long>() {
      @Override
      @NonNull
      public Long call() throws Exception {
        __db.beginTransaction();
        try {
          final Long _result = __insertionAdapterOfReportEntity.insertAndReturnId(report);
          __db.setTransactionSuccessful();
          return _result;
        } finally {
          __db.endTransaction();
        }
      }
    }, $completion);
  }

  @Override
  public Object upsertAll(final List<ReportEntity> reports,
      final Continuation<? super Unit> $completion) {
    return CoroutinesRoom.execute(__db, true, new Callable<Unit>() {
      @Override
      @NonNull
      public Unit call() throws Exception {
        __db.beginTransaction();
        try {
          __upsertionAdapterOfReportEntity.upsert(reports);
          __db.setTransactionSuccessful();
          return Unit.INSTANCE;
        } finally {
          __db.endTransaction();
        }
      }
    }, $completion);
  }

  @Override
  public Object getUnresolved(final Continuation<? super List<ReportEntity>> $completion) {
    final String _sql = "SELECT * FROM reports WHERE resolved = 0 ORDER BY id DESC";
    final RoomSQLiteQuery _statement = RoomSQLiteQuery.acquire(_sql, 0);
    final CancellationSignal _cancellationSignal = DBUtil.createCancellationSignal();
    return CoroutinesRoom.execute(__db, false, _cancellationSignal, new Callable<List<ReportEntity>>() {
      @Override
      @NonNull
      public List<ReportEntity> call() throws Exception {
        final Cursor _cursor = DBUtil.query(__db, _statement, false, null);
        try {
          final int _cursorIndexOfId = CursorUtil.getColumnIndexOrThrow(_cursor, "id");
          final int _cursorIndexOfIssueOrder = CursorUtil.getColumnIndexOrThrow(_cursor, "issueOrder");
          final int _cursorIndexOfPageNum = CursorUtil.getColumnIndexOrThrow(_cursor, "pageNum");
          final int _cursorIndexOfReportType = CursorUtil.getColumnIndexOrThrow(_cursor, "reportType");
          final int _cursorIndexOfDescription = CursorUtil.getColumnIndexOrThrow(_cursor, "description");
          final int _cursorIndexOfResolved = CursorUtil.getColumnIndexOrThrow(_cursor, "resolved");
          final int _cursorIndexOfCreatedAt = CursorUtil.getColumnIndexOrThrow(_cursor, "createdAt");
          final List<ReportEntity> _result = new ArrayList<ReportEntity>(_cursor.getCount());
          while (_cursor.moveToNext()) {
            final ReportEntity _item;
            final int _tmpId;
            _tmpId = _cursor.getInt(_cursorIndexOfId);
            final int _tmpIssueOrder;
            _tmpIssueOrder = _cursor.getInt(_cursorIndexOfIssueOrder);
            final Integer _tmpPageNum;
            if (_cursor.isNull(_cursorIndexOfPageNum)) {
              _tmpPageNum = null;
            } else {
              _tmpPageNum = _cursor.getInt(_cursorIndexOfPageNum);
            }
            final String _tmpReportType;
            _tmpReportType = _cursor.getString(_cursorIndexOfReportType);
            final String _tmpDescription;
            _tmpDescription = _cursor.getString(_cursorIndexOfDescription);
            final boolean _tmpResolved;
            final int _tmp;
            _tmp = _cursor.getInt(_cursorIndexOfResolved);
            _tmpResolved = _tmp != 0;
            final String _tmpCreatedAt;
            _tmpCreatedAt = _cursor.getString(_cursorIndexOfCreatedAt);
            _item = new ReportEntity(_tmpId,_tmpIssueOrder,_tmpPageNum,_tmpReportType,_tmpDescription,_tmpResolved,_tmpCreatedAt);
            _result.add(_item);
          }
          return _result;
        } finally {
          _cursor.close();
          _statement.release();
        }
      }
    }, $completion);
  }

  @Override
  public Flow<List<Integer>> flaggedFlow() {
    final String _sql = "SELECT DISTINCT issueOrder FROM reports WHERE resolved = 0";
    final RoomSQLiteQuery _statement = RoomSQLiteQuery.acquire(_sql, 0);
    return CoroutinesRoom.createFlow(__db, false, new String[] {"reports"}, new Callable<List<Integer>>() {
      @Override
      @NonNull
      public List<Integer> call() throws Exception {
        final Cursor _cursor = DBUtil.query(__db, _statement, false, null);
        try {
          final List<Integer> _result = new ArrayList<Integer>(_cursor.getCount());
          while (_cursor.moveToNext()) {
            final Integer _item;
            _item = _cursor.getInt(0);
            _result.add(_item);
          }
          return _result;
        } finally {
          _cursor.close();
        }
      }

      @Override
      protected void finalize() {
        _statement.release();
      }
    });
  }

  @NonNull
  public static List<Class<?>> getRequiredConverters() {
    return Collections.emptyList();
  }
}
