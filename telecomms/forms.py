from django.forms import ModelForm


from telecomms.models import ATNDataPlans, HonouworldDataPlans, Twins10DataPlans


class ATNDataPlanForm(ModelForm):
    class Meta:
        model = ATNDataPlans
        fields = ['price',]

class Twins10DataPlanForm(ModelForm):
    class Meta:
        model = Twins10DataPlans
        fields = ['price',]

class HonourworldDataPlanForm(ModelForm):
    class Meta:
        model = HonouworldDataPlans
        fields = ['price',]