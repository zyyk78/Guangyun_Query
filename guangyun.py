#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import sqlite3
from typing import List, Dict

DB_NAME = "guangyun.db"

def get_resource_path(relative_path):
    """
    适配 pyinstaller 单文件打包：指向内部虚拟目录（sys._MEIPATH）
    """
    base_path = ""
    if getattr(sys, 'frozen', False):
        # 打包后：指向 pyinstaller 临时解压目录（db 文件在这里）
        base_path = sys._MEIPASS  # 虚拟目录，打包的文件都在这里
    else:
        # 开发环境：指向项目根目录（你的原始 db 位置）
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    full_path = os.path.join(base_path, relative_path)
    # 调试打印
    print(f"打包/开发环境: {'打包后' if getattr(sys, 'frozen', False) else '开发中'}")
    print(f"资源实际路径: {full_path}")
    return full_path

class GuangYunQuery:
    def __init__(self):
        self.db_path = get_resource_path(DB_NAME)
        
        # 检查数据库是否存在
        if not os.path.exists(self.db_path):
            print(f"❌ 错误: 找不到数据库文件")
            print(f"   预期路径: {self.db_path}")
            print(f"   请确保 {DB_NAME} 文件存在")
            sys.exit(1)
            
    SHE_MAP = {
            '1': '通摄', '2': '江摄', '3': '止摄', '4': '遇摄',
            '5': '蟹摄', '6': '臻摄', '7': '山摄', '8': '效摄',
            '9': '果摄', '10': '假摄', '11': '宕摄', '12': '梗摄',
            '13': '曾摄', '14': '流摄', '15': '深摄', '16': '咸摄'
        }

    SHENGDIAO_MAP = {
        'a': '平声',
        'b': '上声', 
        'c': '去声',
        'd': '入声'
    }
    
    # 开合映射
    KAIHE_MAP = {
        'k': '开口',
        'h': '合口'
    }
    
    # 等第映射
    DENGDI_MAP = {
        '1': '一等',
        '2': '二等',
        '3': '三等',
        '4': '四等',
        '3a': '重钮四等',
        '3b': '重钮三等'
    }
    
    def _get_unicode_hex(self, char: str) -> str:
        """将汉字转换为Unicode编码"""
        return f"{ord(char):04X}"
    def search_character(self, character: str) -> List[Dict]:
        if not character or len(character.strip()) != 1:
            return []
        
        seen = set()
        
        unicode_hex = self._get_unicode_hex(character.strip()[0])
        
        all_results = []
        
        # 1. 查询正字 (chrucs)
        results = self._search_by_field('chrucs', unicode_hex, result_type=1)
        for r in results:
            # 用原字作为去重依据
            key = r.get('hanzi', '')
            if key not in seen:
                seen.add(key)
                all_results.append(r)
        
        # 2. 查询简体字 (jucs) - 即使有正字结果也继续搜索
        results = self._search_by_field('jucs', unicode_hex, result_type=2)
        for r in results:
            key = r.get('hanzi', '')
            if key not in seen:
                seen.add(key)
                # 添加关系说明：这个字是某个正字的简体字源头
                r['relation_note'] = f"「{character}」是「{r['hanzi']}」的简体字"
                all_results.append(r)
        
        # 3. 查询异体字1 (v1ucs)
        results = self._search_by_field('v1ucs', unicode_hex, result_type=3)
        for r in results:
            key = r.get('hanzi', '')
            if key not in seen:
                seen.add(key)
                # 添加关系说明
                r['relation_note'] = f"「{character}」是「{r['hanzi']}」的异体字"
                all_results.append(r)
        
        # 4. 查询异体字2 (v2ucs)
        results = self._search_by_field('v2ucs', unicode_hex, result_type=3)
        for r in results:
            key = r.get('hanzi', '')
            if key not in seen:
                seen.add(key)
                r['relation_note'] = f"「{character}」是「{r['hanzi']}」的异体字"
                all_results.append(r)
        
        return all_results

    def _search_by_field(self, field: str, value: str, result_type: int) -> List[Dict]:
        """
        按指定字段搜索
        """
        sql = """
            SELECT 
                -- PHON表基础信息
                phon.chr as hanzi,
                phon.mi as shengmu,
                phon.mt as shengdiao,
                phon.kh as kaihe,
                phon.mf as yunbu,
                phon.mg as phon_she,
                phon.gr as dengdi,
                phon.fq as fanqie,
                phon.nt as beizhu,
                phon.note as zhushi,
                phon.page as page,
                phon.j as jianti,
                phon.v1 as yitizi1,
                phon.v2 as yitizi2,
                phon.chrucs,
                phon.jucs,
                phon.v1ucs,
                phon.v2ucs,
                
                min1.gbh as gao_benhan,      -- 高本汉
                min1.wl as wang_li,           -- 王力
                min1.dth as dong_tonghe,      -- 董同龢
                min1.zfg as zhou_fagao,       -- 周法高
                min1.lr as li_rong,           -- 李荣
                min1.srf as shao_rongfen,     -- 邵荣芬
                min1.plb as puli_ben,         -- 蒲立本
                min1.pwy as pan_wuyun,        -- 潘悟云
                min1.lfg as li_fanggui,       -- 李方桂
                
                Mfn.gbh as gao_benhan_1,
                Mfn.wl as wang_li_1,
                Mfn.dth as dong_tonghe_1,
                Mfn.zfg as zhou_fagao_1,
                Mfn.lr as li_rong_1,
                Mfn.srf as shao_rongfen_1,
                Mfn.plb as puli_ben_1,
                Mfn.pwy as pan_wuyun_1,
                Mfn.lfg as li_fanggui_1,
                
                -- Mfn表的摄
                Mfn.mg as mfn_she
                
            FROM MIN1 
            INNER JOIN (
                MFN 
                INNER JOIN PHON 
                ON MFN.MF = PHON.MF 
                AND MFN.GR = PHON.GR 
                AND MFN.KH = PHON.KH
            ) ON MIN1.MI = PHON.MI 
            WHERE PHON.{} = ?
        """.format(field)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql, (value,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                # 标记结果类型
                result['result_type'] = ['正字', '简体字', '异体字'][result_type-1]
                result['result_type_code'] = result_type
                
                # 摄的优先级：先用 Mfn.mg，没有再用 PHON.mg
                if result.get('mfn_she') and str(result['mfn_she']).strip():
                    result['she'] = result['mfn_she']
                else:
                    result['she'] = result.get('phon_she', '')
                
                results.append(result)
            
            conn.close()
            return results
            
        except sqlite3.Error as e:
            print(f"数据库错误: {e}")
            return []
            

    def print_results(self, results: List[Dict]):
        """打印查询结果（包含各家拟音）"""
        if not results:
            print("❌ 未找到记录")
            return
        
        # 学者名字映射（用于显示）
        SCHOLAR_NAMES = {
            'gao_benhan': '高本汉',
            'wang_li': '王力',
            'dong_tonghe': '董同龢',
            'zhou_fagao': '周法高',
            'li_rong': '李荣',
            'shao_rongfen': '邵荣芬',
            'puli_ben': '蒲立本',
            'pan_wuyun': '潘悟云',
            'li_fanggui': '李方桂'
        }
        
        print(f"\n🔍 共找到 {len(results)} 条记录\n")
        
        for i, r in enumerate(results, 1):
            print(f"【记录 {i}】{'-' * 70}")
            print(f"📝 汉字: {r.get('hanzi', 'N/A')}")
            print(f"🏷️  类型: {r.get('result_type', 'N/A')}")
            print(f"🔊 声母: {r.get('shengmu', 'N/A')}母")
            print(f"🎵 声调: {self.SHENGDIAO_MAP.get(r.get('shengdiao', ''), r.get('shengdiao', 'N/A'))}")
            print(f"↔️  开合: {self.KAIHE_MAP.get(r.get('kaihe', ''), r.get('kaihe', 'N/A'))}")
            print(f"📖 韵部: {r.get('yunbu', 'N/A')}韵")
            print(f"📚  摄 : {self.SHE_MAP.get(str(r.get('she', '')), r.get('she', 'N/A'))}摄")
            print(f"⚖️  等第: {self.DENGDI_MAP.get(r.get('dengdi', ''), r.get('dengdi', 'N/A'))}")
            
            if r.get('fanqie'):
                print(f"🔄 反切: {r['fanqie']}")
            
            # 显示各家拟音
            print(f"\n  【中古音各家拟音】")
            has_niyin = False
            
            for field, name in SCHOLAR_NAMES.items():
                value = r.get(field)+r.get(field+'_1')
                
                if value and str(value).strip():
                    print(f"    {name}: {value}")
                    has_niyin = True
            
            if not has_niyin:
                print("    无拟音数据")
            
            print()
            print(f"备注: {r.get('beizhu', 'N/A')}")
            print()
    
def is_chinese_char_extended(char: str) -> bool:
    """判断是否为汉字（扩展范围）"""
    if len(char) != 1:
        return False
    code = ord(char)
    # 汉字Unicode范围：
    # 基本汉字：4E00-9FFF
    # 扩展A：3400-4DBF
    # 扩展B：20000-2A6DF
    # 等等...
    return (0x4E00 <= code <= 0x9FFF) or \
           (0x3400 <= code <= 0x4DBF) or \
           (0x20000 <= code <= 0x2A6DF)
           
def main():
    query = GuangYunQuery()
    print("=" * 60)
    print("广韵查询系统 - 输入'q'或'quit'退出")
    print("=" * 60)
    
    while True:
        try:
            # 读入输入
            user_input = input("\n请输入要查询的汉字: ").strip()
            
            # 检查退出条件
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("再见！")
                break
            
            # 检查是否为空
            if not user_input:
                print("❌ 输入不能为空，请重新输入")
                continue
            
            # 检查是否为单个汉字
            if len(user_input) != 1:
                print(f"❌ 请输入单个汉字（当前输入了 {len(user_input)} 个字符）")
                continue
            
            # 检查是否为汉字
            if not is_chinese_char_extended(user_input):
                print(f"❌ '{user_input}' 不是汉字，请输入汉字")
                continue
            
            # 执行查询
            print(f"\n🔍 正在查询: {user_input}")
            results = query.search_character(user_input)
            query.print_results(results)
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            
if __name__ == "__main__":
    main()