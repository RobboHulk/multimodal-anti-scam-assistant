package com.juntong.multimodalantiscamassistant.module.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.juntong.multimodalantiscamassistant.module.user.entity.User;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;
import java.util.List;

@Mapper
public interface UserMapper extends BaseMapper<User> {

    /** 绕过逻辑删除，直接检查用户名是否存在 */
    @Select("SELECT COUNT(1) > 0 FROM user WHERE username = #{username}")
    boolean usernameExists(String username);

    /** 管理员查全部用户（绕过逻辑删除） */
    @Select("SELECT * FROM user ORDER BY created_at DESC")
    List<User> selectAllIncludingDeleted();

    /** 注册时手动插入，确保 password 与 avatar 字段写入 */
    @Insert("INSERT INTO user (username, password, phone, avatar, age_group, risk_preference, risk_threshold, intervention_strategy, created_at, updated_at) " +
            "VALUES (#{username}, #{password}, #{phone}, #{avatar}, #{ageGroup}, #{riskPreference}, #{riskThreshold}, #{interventionStrategy}, NOW(), NOW())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insertUser(User user);
}
