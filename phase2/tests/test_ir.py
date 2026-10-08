import unittest

from campusflow.ir import IRGenerator, format_ir
from campusflow.lexer import Lexer
from campusflow.parser import Parser


def generate(source):
    parsed = Parser(Lexer(source).scan().tokens).parse()
    assert not parsed.errors
    return IRGenerator().generate(parsed.program)


class IrTests(unittest.TestCase):
    def test_lowers_straight_line_statements(self):
        program = generate("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Hall FOR Demo CAPACITY 50;",
            "ASSIGN Projector TO Demo;",
            "CANCEL Demo;",
        ]))
        self.assertEqual(
            [instruction.opcode for instruction in program.instructions],
            [
                "CREATE_EVENT",
                "RESERVE_RESOURCE",
                "ASSIGN_ITEM",
                "CANCEL_EVENT",
            ],
        )
        self.assertEqual(
            program.instructions[1].operands,
            ("Hall", "Demo", 50),
        )

    def test_lowers_if_to_jump_body_and_label(self):
        program = generate(
            "IF capacity >= 100 THEN RESERVE Hall FOR Demo CAPACITY 120;"
        )
        self.assertEqual(
            [instruction.opcode for instruction in program.instructions],
            ["JUMP_IF_FALSE", "RESERVE_RESOURCE", "LABEL"],
        )
        jump, _, label = program.instructions
        self.assertEqual(jump.operands[:2], (">=", 100))
        self.assertEqual(jump.operands[2], label.operands[0])

    def test_format_numbers_instructions_and_source_positions(self):
        formatted = format_ir(generate("CANCEL Demo;"))
        self.assertEqual(formatted, "0000  CANCEL_EVENT 'Demo'  @1:1")


if __name__ == "__main__":
    unittest.main()
